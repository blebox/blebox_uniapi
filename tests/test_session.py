"""Tests for `blebox_uniapi` package."""

import pytest
import logging
import aiohttp

from unittest.mock import patch, Mock, AsyncMock

from blebox_uniapi.session import CONNECT_TIMEOUT, ApiHost as Session
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

    client.get.assert_called_once_with(
        "http://127.0.0.4:88/api/foo",
        timeout=aiohttp.ClientTimeout(total=2, sock_connect=CONNECT_TIMEOUT),
    )

    assert result == 123


async def test_session_default_client_created(mocked_client, logger):
    mocked_client.get = AsyncMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", 2, None, None, logger)

    result = await api_session.async_api_get("/api/foo")

    mocked_client.get.assert_called_once_with(
        "http://127.0.0.4:88/api/foo",
        timeout=aiohttp.ClientTimeout(total=2, sock_connect=CONNECT_TIMEOUT),
    )
    assert result == 123


async def test_session_default_timeout_used(mocked_client, logger):
    mocked_client.get = AsyncMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", None, None, None, logger)

    await api_session.async_api_get("/api/foo")
    expected_timeout = aiohttp.ClientTimeout(
        total=None, connect=None, sock_read=5, sock_connect=CONNECT_TIMEOUT
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


async def test_session_retries_after_connection_timeout(logger, client):
    client.get = AsyncMock(
        side_effect=[aiohttp.ConnectionTimeoutError(), valid_response()]
    )
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    result = await api_session.async_api_get("/api/foo")

    assert result == 123
    assert client.get.call_count == 2


async def test_session_post_retries_after_connection_timeout(logger, client):
    client.post = AsyncMock(
        side_effect=[aiohttp.ConnectionTimeoutError(), valid_response()]
    )
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    result = await api_session.async_api_post("/api/foo", {"a": 1})

    assert result == 123
    assert client.post.call_count == 2
    client.post.assert_called_with(
        "http://127.0.0.4:88/api/foo",
        timeout=aiohttp.ClientTimeout(total=2, sock_connect=CONNECT_TIMEOUT),
        data={"a": 1},
    )


async def test_session_connection_timeout_after_all_attempts(logger, client):
    client.get = AsyncMock(side_effect=aiohttp.ConnectionTimeoutError())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    with pytest.raises(
        error.TimeoutError,
        match=rf"Failed to connect to 127\.0\.0\.4:88 within {CONNECT_TIMEOUT}s",
    ):
        await api_session.async_api_get("/api/foo")

    assert client.get.call_count == 2


async def test_session_read_timeout_is_not_retried(logger, client):
    client.get = AsyncMock(side_effect=aiohttp.SocketTimeoutError())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    with pytest.raises(
        error.TimeoutError,
        match=r"Request to http://127\.0\.0\.4:88/api/foo timed out",
    ):
        await api_session.async_api_get("/api/foo")

    client.get.assert_called_once()


async def test_session_client_timeout_passed_through(logger, client):
    client.get = AsyncMock(return_value=valid_response())
    timeout = aiohttp.ClientTimeout(total=7, sock_connect=1)
    api_session = Session("127.0.0.4", "88", timeout, client, None, logger)

    await api_session.async_api_get("/api/foo")

    client.get.assert_called_once_with("http://127.0.0.4:88/api/foo", timeout=timeout)


async def test_session_connection_timeout_message_uses_connect(logger, client):
    client.get = AsyncMock(side_effect=aiohttp.ConnectionTimeoutError())
    timeout = aiohttp.ClientTimeout(total=10, connect=4)
    api_session = Session("127.0.0.4", "88", timeout, client, None, logger)

    with pytest.raises(
        error.TimeoutError, match=r"Failed to connect to 127\.0\.0\.4:88 within 4s"
    ):
        await api_session.async_api_get("/api/foo")
