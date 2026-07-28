"""Tests for `blebox_uniapi` package."""

import pytest
import logging
import aiohttp

from unittest.mock import patch, Mock, AsyncMock

from blebox_uniapi.session import ApiHost as Session
from blebox_uniapi import error


@pytest.fixture
def mocked_client():
    with patch("aiohttp.ClientSession", spec_set=True, autospec=True) as mocked_session:
        yield mocked_session.return_value


@pytest.fixture
def logger():
    return Mock(spec_set=logging.Logger).return_value


@pytest.fixture
def client():
    return Mock(spec_set=aiohttp.ClientSession)


def valid_response():
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = 200
    response.content_type = "application/json"
    response.text = AsyncMock(return_value="foobar")
    response.json = AsyncMock(return_value=123)
    return response


def timeout_error(connection, timeout):
    raise aiohttp.ServerTimeoutError


def client_error(connection, timeout):
    raise aiohttp.ClientError("client err")


def os_error(connection, timeout):
    raise aiohttp.ClientOSError("os error")


def bad_http_response(spec_set=aiohttp.ClientResponse):
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = 400
    return response


async def test_session_api_get(logger, client):
    client.get = AsyncMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    result = await api_session.async_api_get("/api/foo")

    client.get.assert_called_once_with("http://127.0.0.4:88/api/foo", timeout=2)

    assert result == 123


async def test_session_default_client_created(mocked_client, logger):
    mocked_client.get = AsyncMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", 2, None, None, logger)

    result = await api_session.async_api_get("/api/foo")

    mocked_client.get.assert_called_once_with("http://127.0.0.4:88/api/foo", timeout=2)
    assert result == 123


async def test_session_default_timeout_used(mocked_client, logger):
    mocked_client.get = AsyncMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", None, None, None, logger)

    await api_session.async_api_get("/api/foo")
    expected_timeout = aiohttp.ClientTimeout(
        total=None, connect=None, sock_read=5, sock_connect=5
    )

    mocked_client.get.assert_called_once_with(
        "http://127.0.0.4:88/api/foo", timeout=expected_timeout
    )


async def test_session_api_get_timeout(logger, client):
    client.get = AsyncMock(side_effect=timeout_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    with pytest.raises(error.TimeoutError):
        await api_session.async_api_get("/api/foo")


async def test_session_api_post_timeout(logger, client):
    def post_timeout_error(connection, **kwargs):
        timeout_error(connection, timeout=kwargs.get("timeout"))

    client.post = AsyncMock(side_effect=post_timeout_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    with pytest.raises(error.TimeoutError):
        await api_session.async_api_post("/api/foo", {})


async def test_session_api_get_client_error(logger, client):
    client.get = AsyncMock(side_effect=client_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(
        error.ClientError,
        match=r"API request http://127\.0\.0\.4:88/api/foo failed: client err",
    ):
        await api_session.async_api_get("/api/foo")


async def test_session_always_show_address_details(logger, client):
    client.get = AsyncMock(side_effect=os_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(
        error.ConnectionError, match=r"Failed to connect to 127\.0\.0\.4:88: os error"
    ):
        await api_session.async_api_get("/api/foo")


async def test_session_api_post_client_error(logger, client):
    def post_client_error(connection, **kwargs):
        client_error(connection, timeout=kwargs.get("timeout"))

    client.post = AsyncMock(side_effect=post_client_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.ClientError):
        await api_session.async_api_post("/api/foo", {})


async def test_session_api_get_http_error(logger, client):
    client.get = AsyncMock(return_value=bad_http_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.HttpError):
        await api_session.async_api_get("/api/foo")


async def test_session_api_post_http_error(logger, client):
    client.post = AsyncMock(return_value=bad_http_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.HttpError):
        await api_session.async_api_post("/api/foo", {})


async def test_session_provides_a_logger(logger, client):
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    api_session.logger.debug("foobar")
    logger.debug.assert_called_once_with("foobar")


def ota_accepted_response(status=202):
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = status
    response.content_type = None
    return response


def unauthorized_response():
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = 401
    return response


def non_json_response():
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = 200
    response.content_type = None
    return response


async def test_session_api_get_ota_accepts_202_without_body(logger, client):
    client.get = AsyncMock(return_value=ota_accepted_response(status=202))
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    result = await api_session.async_api_get_ota("/api/ota/check")
    assert result is None


async def test_session_api_get_ota_accepts_204_no_content(logger, client):
    client.get = AsyncMock(return_value=ota_accepted_response(status=204))
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    result = await api_session.async_api_get_ota("/api/ota/check")
    assert result is None


async def test_session_api_get_ota_rejects_400(logger, client):
    client.get = AsyncMock(return_value=bad_http_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.HttpError):
        await api_session.async_api_get_ota("/api/ota/check")


async def test_session_api_get_unauthorized(logger, client):
    client.get = AsyncMock(return_value=unauthorized_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.UnauthorizedRequest):
        await api_session.async_api_get("/api/device/state")


async def test_session_api_get_ota_unauthorized(logger, client):
    client.get = AsyncMock(return_value=unauthorized_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.UnauthorizedRequest):
        await api_session.async_api_get_ota("/api/ota/check")


async def test_session_api_get_non_json_returns_none(logger, client):
    client.get = AsyncMock(return_value=non_json_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    result = await api_session.async_api_get("/api/device/state")
    assert result is None


async def test_session_api_get_unicode_decode_error_raises_connection_error(
    logger, client
):
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = 200
    response.content_type = "application/json"
    response.json = AsyncMock(
        side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
    )
    client.get = AsyncMock(return_value=response)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.ConnectionError, match="Invalid response encoding"):
        await api_session.async_api_get("/api/device/state")
