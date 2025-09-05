from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Iterable, Literal, Optional, override
from urllib.parse import urljoin

from pardner.exceptions import UnsupportedRequestException, UnsupportedVerticalException
from pardner.services import BaseTransferService
from pardner.services.utils import scope_as_set, scope_as_string
from pardner.verticals import PhysicalActivityVertical, SocialPostingVertical, Vertical
from pardner.verticals.sub_verticals import AssociatedMediaSubVertical


class StravaTransferService(BaseTransferService):
    """
    Class responsible for obtaining end-user authorization to make requests to
    Strava's API.
    See API documentation: https://developers.strava.com/docs/reference/
    """

    _authorization_url = 'https://www.strava.com/oauth/authorize'
    _base_url = 'https://www.strava.com/api/v3/'
    _token_url = 'https://www.strava.com/oauth/token'

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        state: Optional[str] = None,
        verticals: set[Vertical] = set(),
    ) -> None:
        super().__init__(
            service_name='Strava',
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            state=state,
            supported_verticals={PhysicalActivityVertical},
            verticals=verticals,
        )

    @property
    def scope(self) -> set[str]:
        return scope_as_set(self._oAuth2Session.scope, delimiter=',')

    @scope.setter
    def scope(self, new_scope: Iterable[str] | str) -> None:
        self._oAuth2Session.scope = scope_as_string(new_scope, delimiter=',')

    @override
    def fetch_token(
        self,
        code: Optional[str] = None,
        authorization_response: Optional[str] = None,
        include_client_id: bool = True,
    ) -> dict[str, Any]:
        return super().fetch_token(code, authorization_response, include_client_id)

    @override
    def scope_for_verticals(self, verticals: Iterable[Vertical]) -> set[str]:
        sub_scopes: set[str] = set()
        for vertical in verticals:
            if not self.is_vertical_supported(vertical):
                raise UnsupportedVerticalException(
                    vertical, service_name=self._service_name
                )
            if vertical == PhysicalActivityVertical:
                sub_scopes.update(['activity:read', 'profile:read_all'])
        return sub_scopes

    def _convert_to_datetime(self, raw_datetime: str | None) -> datetime | None:
        if raw_datetime:
            return datetime.strptime(raw_datetime, '%Y-%m-%dT%H:%M:%SZ')
        return None

    def _parse_social_posting(self, raw_data: Any) -> SocialPostingVertical | None:
        """
        Given the response from the API request, creates a
        :class:`SocialPostingVertical` model object, if possible.

        :param raw_data: the JSON representation of the data returned by the request.

        :returns: :class:`SocialPostingVertical` or ``None``, depending on whether it
        was possible to extract data from the response
        """
        if not isinstance(raw_data, dict):
            return None
        raw_data_dict = defaultdict(dict, raw_data)

        created_at = raw_data_dict.get('start_date')
        if created_at:
            created_at = self._convert_to_datetime(created_at)

        url_str = urljoin(
            'https://www.strava.com/activities/', str(raw_data_dict.get('id'))
        )
        interaction_count = raw_data_dict.get('kudos_count', 0) + raw_data_dict.get(
            'comment_count', 0
        )

        status: Literal['public', 'private', 'restricted'] = 'public'
        if raw_data_dict.get('private'):
            status = 'private'
        elif raw_data_dict.get('visibility') == 'followers_only':
            status = 'restricted'

        associated_media_list = []
        if raw_data_dict.get('total_photo_count', 0) > 0:
            photo_urls = (
                raw_data_dict['photos'].get('primary', {}).get('urls', {}).values()
            )
            associated_media_list = [
                AssociatedMediaSubVertical(image_url=photo_url)
                for photo_url in photo_urls
            ]

        return SocialPostingVertical(
            creator_user_id=str(raw_data_dict['athlete'].get('id')),
            service=self._service_name,
            created_at=created_at,
            url=url_str,
            associated_media=associated_media_list,
            interaction_count=interaction_count,
            status=status,
            text=raw_data_dict.get('description'),
            title=raw_data_dict.get('name'),
        )

    def fetch_social_posting_vertical(
        self, request_params: dict[str, Any] = {}, count: int = 30
    ) -> tuple[list[SocialPostingVertical | None], Any]:
        """
        Fetches and returns social postings created by the authorized user.

        :param count: number of posts to request. At most 30 at a time.
        :param request_params: any other endpoint-specific parameters to be sent
        to the endpoint. Depending on the parameters passed, this could override
        the other arguments to this method.

        :returns: two elements: the first, a list of :class:`SocialPostingVertical`s
        or ``None``, if unable to parse; the second, the raw response from making the
        request.

        :raises: :class:`UnsupportedRequestException` if the request is unable to be
        made.
        """
        max_count = 30
        if count <= max_count:
            raw_social_postings = self._get_resource_from_path(
                'athlete/activities', params={'per_page': count, **request_params}
            ).json()
            return [
                self._parse_social_posting(raw_social_posting)
                for raw_social_posting in raw_social_postings
            ], raw_social_postings
        raise UnsupportedRequestException(
            self._service_name,
            f'can only make a request for at most {max_count} posts at a time.',
        )

    def _parse_physical_activity(
        self, raw_data: Any
    ) -> PhysicalActivityVertical | None:
        """
        Given the response from the API request, creates a
        :class:`PhysicalActivityVertical` model object, if possible.

        :param raw_data: the JSON representation of the data returned by the request.

        :returns: :class:`PhysicalActivityVertical` or ``None``, depending on whether it
        was possible to extract data from the response
        """
        social_posting = self._parse_social_posting(raw_data)
        if not social_posting:
            return None

        social_posting_dict = social_posting.model_dump()
        raw_data_dict = defaultdict(dict, raw_data)

        start_datetime = self._convert_to_datetime(raw_data_dict.get('start_date'))
        duration_s = raw_data_dict.get('elapsed_time')
        duration_timedelta = timedelta(seconds=duration_s) if duration_s else None
        end_datetime = (
            start_datetime + duration_timedelta
            if start_datetime and duration_timedelta
            else None
        )

        start_latlng = raw_data_dict.get('start_latlng')
        end_latlng = raw_data_dict.get('end_latlng')

        social_posting_dict.update(
            {
                'vertical_name': 'physical_activity',
                'activity_type': raw_data_dict.get('sport_type'),
                'distance': raw_data_dict.get('distance'),
                'elevation_high': raw_data_dict.get('elev_high'),
                'elevation_low': raw_data_dict.get('elev_low'),
                'kilocalories': raw_data_dict.get('calories'),
                'max_speed': raw_data_dict.get('max_speed'),
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'start_latitude': start_latlng[0] if start_latlng else None,
                'start_longitude': start_latlng[1] if start_latlng else None,
                'end_latitude': end_latlng[0] if end_latlng else None,
                'end_longitude': end_latlng[1] if end_latlng else None,
            }
        )

        return PhysicalActivityVertical.model_validate(social_posting_dict)

    def fetch_physical_activity_vertical(
        self, request_params: dict[str, Any] = {}, count: int = 30
    ) -> tuple[list[PhysicalActivityVertical | None], Any]:
        """
        Fetches and returns activities completed by the authorized user.

        :param count: number of activities to request. At most 30 at a time.
        :param request_params: any other endpoint-specific parameters to be sent
        to the endpoint. Depending on the parameters passed, this could override
        the other arguments to this method.

        :returns: two elements: the first, a list of :class:`PhysicalActivityVertical`s
        or ``None``, if unable to parse; the second, the raw response from making the
        request.

        :raises: :class:`UnsupportedRequestException` if the request is unable to be
        made.
        """
        max_count = 30
        if count <= max_count:
            raw_activities = self._get_resource_from_path(
                'athlete/activities', params={'per_page': count, **request_params}
            ).json()
            return [
                self._parse_physical_activity(raw_activity)
                for raw_activity in raw_activities
            ], raw_activities
        raise UnsupportedRequestException(
            self._service_name,
            f'can only make a request for at most {max_count} activities at a time.',
        )
