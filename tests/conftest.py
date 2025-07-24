from typing import Any
from urllib import parse

import pytest


@pytest.fixture
def mock_outbound_requests(mocker):
    mock_oauth2session_request = mocker.patch('requests_oauthlib.OAuth2Session.request')
    mock_client_parse_request_body_response = mocker.patch(
        'oauthlib.oauth2.rfc6749.clients.WebApplicationClient.parse_request_body_response'
    )
    return (mock_oauth2session_request, mock_client_parse_request_body_response)


def get_url_params(url: str) -> dict[str, Any]:
    url_query = parse.urlsplit(url).query
    return dict(parse.parse_qsl(url_query))
