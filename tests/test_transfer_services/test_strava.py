import datetime

import pytest
from pydantic import AnyHttpUrl
from requests import HTTPError

from pardner.exceptions import UnsupportedRequestException, UnsupportedVerticalException
from pardner.verticals.physical_activity import PhysicalActivityVertical
from tests.test_transfer_services.conftest import (
    NewVertical,
    dump_and_filter_model_objs,
    mock_oauth2_session_get,
)


def test_scope(strava_transfer_service):
    strava_transfer_service.scope == 'activity:read,profile:read_all'


@pytest.mark.parametrize(
    ['verticals', 'expected_scope'],
    [([], set()), ([PhysicalActivityVertical], {'activity:read', 'profile:read_all'})],
)
def test_scope_for_verticals(strava_transfer_service, verticals, expected_scope):
    assert strava_transfer_service.scope_for_verticals(verticals) == expected_scope


def test_scope_for_verticals_raises_error(strava_transfer_service):
    with pytest.raises(UnsupportedVerticalException):
        strava_transfer_service.scope_for_verticals([NewVertical])


def test_fetch_physical_activity_raises_exception(strava_transfer_service):
    with pytest.raises(UnsupportedRequestException):
        strava_transfer_service.fetch_physical_activity_vertical(count=31)


def test_fetch_physical_activity_vertical_raises_http_exception(
    strava_transfer_service, mock_oauth2_session_get_bad_response
):
    with pytest.raises(HTTPError):
        strava_transfer_service.fetch_physical_activity_vertical()


def test_fetch_physical_activity_vertical(mocker, strava_transfer_service):
    # Adapted from
    # https://developers.strava.com/docs/reference/#api-Activities-getLoggedInAthleteActivities
    sample_response = [
        {
            'resource_state': 2,
            'athlete': {'id': 134815, 'resource_state': 1},
            'name': 'Happy Friday',
            'distance': 24931.4,
            'moving_time': 4500,
            'elapsed_time': 4500,
            'total_elevation_gain': 0,
            'type': 'Ride',
            'sport_type': 'Hike',
            'workout_type': None,
            'id': 154504250376823,
            'external_id': 'garmin_push_12345678987654321',
            'upload_id': 987654321234567891234,
            'description': 'mock description',
            'start_date': '2018-05-02T12:15:09Z',
            'start_date_local': '2018-05-02T05:15:09Z',
            'timezone': '(GMT-08:00) America/Los_Angeles',
            'calories': 870.2,
            'utc_offset': -25200,
            'start_latlng': [41.41, -41.41],
            'end_latlng': [42.42, -42.42],
            'location_city': None,
            'location_state': None,
            'location_country': 'United States',
            'achievement_count': 0,
            'kudos_count': 3,
            'comment_count': 1,
            'athlete_count': 1,
            'photo_count': 0,
            'map': {
                'id': 'a12345678987654321',
                'summary_polyline': None,
                'resource_state': 2,
            },
            'trainer': True,
            'commute': False,
            'manual': False,
            'private': False,
            'visibility': 'followers_only',
            'flagged': False,
            'gear_id': 'b12345678987654321',
            'from_accepted_tag': False,
            'average_speed': 5.54,
            'max_speed': 11,
            'average_cadence': 67.1,
            'average_watts': 175.3,
            'weighted_average_watts': 210,
            'kilojoules': 788.7,
            'device_watts': True,
            'has_heartrate': True,
            'average_heartrate': 140.3,
            'max_heartrate': 178,
            'max_watts': 406,
            'pr_count': 0,
            'total_photo_count': 1,
            'photos': {
                'primary': {'urls': {'1': 'https://url1.com', '2': 'https://url2.com'}}
            },
            'has_kudoed': False,
            'suffer_score': 82,
        },
        {
            'resource_state': 2,
            'athlete': {'id': 167560, 'resource_state': 1},
            'name': 'Bondcliff',
            'distance': 23676.5,
            'moving_time': 5400,
            'elapsed_time': 5400,
            'total_elevation_gain': 0,
            'type': 'Ride',
            'sport_type': 'MountainBikeRide',
            'workout_type': None,
            'id': 1234567809,
            'external_id': 'garmin_push_12345678987654321',
            'upload_id': 1234567819,
            'start_date': '2018-04-30T12:35:51Z',
            'start_date_local': '2018-04-30T05:35:51Z',
            'timezone': '(GMT-08:00) America/Los_Angeles',
            'utc_offset': -25200,
            'start_latlng': None,
            'end_latlng': None,
            'location_city': None,
            'location_state': None,
            'location_country': 'United States',
            'achievement_count': 0,
            'kudos_count': 4,
            'comment_count': 0,
            'elev_high': 182.5,
            'elev_low': 179.9,
            'athlete_count': 1,
            'photo_count': 0,
            'map': {'id': 'a12345689', 'summary_polyline': None, 'resource_state': 2},
            'trainer': True,
            'commute': False,
            'manual': False,
            'private': False,
            'flagged': False,
            'gear_id': 'b12345678912343',
            'from_accepted_tag': False,
            'average_speed': 4.385,
            'max_speed': 8.8,
            'average_cadence': 69.8,
            'average_watts': 200,
            'weighted_average_watts': 214,
            'kilojoules': 1080,
            'device_watts': True,
            'has_heartrate': True,
            'average_heartrate': 152.4,
            'max_heartrate': 183,
            'max_watts': 403,
            'pr_count': 0,
            'total_photo_count': 1,
            'has_kudoed': False,
            'suffer_score': 162,
        },
    ]

    response_object = mocker.MagicMock()
    response_object.json.return_value = sample_response

    oauth2_session_get = mock_oauth2_session_get(mocker, response_object)

    model_objs, _ = strava_transfer_service.fetch_physical_activity_vertical()
    model_obj_dumps = dump_and_filter_model_objs(model_objs)

    assert (
        oauth2_session_get.call_args.args[1]
        == 'https://www.strava.com/api/v3/athlete/activities'
    )

    base_model_dict = {
        'service': 'Strava',
        'vertical_name': 'physical_activity',
        'abstract': None,
        'associated_media': [],
        'interaction_count': 4,
        'keywords': [],
        'shared_content': [],
        'text': None,
        'elevation_high': None,
        'elevation_low': None,
        'kilocalories': None,
        'start_latitude': None,
        'start_longitude': None,
        'end_latitude': None,
        'end_longitude': None,
    }

    assert model_obj_dumps == [
        {
            **base_model_dict,
            'service_object_id': '154504250376823',
            'creator_user_id': '134815',
            'data_owner_id': '134815',
            'created_at': datetime.datetime(2018, 5, 2, 12, 15, 9),
            'url': AnyHttpUrl('https://www.strava.com/activities/154504250376823'),
            'associated_media': [
                {'media_type': 'image', 'url': AnyHttpUrl('https://url1.com/')},
                {'media_type': 'image', 'url': AnyHttpUrl('https://url2.com/')},
            ],
            'status': 'restricted',
            'text': 'mock description',
            'title': 'Happy Friday',
            'activity_type': 'Hike',
            'distance': 24931.4,
            'kilocalories': 870.2,
            'max_speed': 11.0,
            'start_datetime': datetime.datetime(2018, 5, 2, 12, 15, 9),
            'start_latitude': 41.41,
            'start_longitude': -41.41,
            'end_datetime': datetime.datetime(2018, 5, 2, 13, 30, 9),
            'end_latitude': 42.42,
            'end_longitude': -42.42,
        },
        {
            **base_model_dict,
            'service_object_id': '1234567809',
            'creator_user_id': '167560',
            'data_owner_id': '167560',
            'created_at': datetime.datetime(2018, 4, 30, 12, 35, 51),
            'url': AnyHttpUrl('https://www.strava.com/activities/1234567809'),
            'status': 'public',
            'title': 'Bondcliff',
            'activity_type': 'MountainBikeRide',
            'distance': 23676.5,
            'elevation_high': 182.5,
            'elevation_low': 179.9,
            'max_speed': 8.8,
            'start_datetime': datetime.datetime(2018, 4, 30, 12, 35, 51),
            'end_datetime': datetime.datetime(2018, 4, 30, 14, 5, 51),
        },
    ]
