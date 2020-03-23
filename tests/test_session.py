#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `blebox_uniapi` package."""

import pytest
import logging
import aiohttp

from asynctest import patch, Mock, CoroutineMock

from blebox_uniapi.session import ApiHost as Session
from blebox_uniapi import error

pytestmark = pytest.mark.asyncio


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
    response.text = CoroutineMock(return_value="foobar")
    response.json = CoroutineMock(return_value=123)
    return response


def timeout_error(connection, timeout):
    raise aiohttp.ServerTimeoutError


def client_error(connection, timeout):
    raise aiohttp.ClientError


def bad_http_response(spec_set=aiohttp.ClientResponse):
    response = Mock(spec_set=aiohttp.ClientResponse)
    response.status = 401
    return response


async def test_session_api_get(logger, client):
    client.get = CoroutineMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    result = await api_session.async_api_get("/api/foo")

    client.get.assert_called_once_with("http://127.0.0.4:88/api/foo", timeout=2)

    assert result == 123


async def test_session_default_client_created(mocked_client, logger):
    mocked_client.get = CoroutineMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", 2, None, None, logger)

    result = await api_session.async_api_get("/api/foo")

    mocked_client.get.assert_called_once_with("http://127.0.0.4:88/api/foo", timeout=2)
    assert result == 123


async def test_session_default_timeout_used(mocked_client, logger):
    mocked_client.get = CoroutineMock(return_value=valid_response())
    api_session = Session("127.0.0.4", "88", None, None, None, logger)

    await api_session.async_api_get("/api/foo")
    expected_timeout = aiohttp.ClientTimeout(
        total=None, connect=None, sock_read=5, sock_connect=5
    )

    mocked_client.get.assert_called_once_with(
        "http://127.0.0.4:88/api/foo", timeout=expected_timeout
    )


async def test_session_api_get_timeout(logger, client):
    client.get = CoroutineMock(side_effect=timeout_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    with pytest.raises(error.TimeoutError):
        await api_session.async_api_get("/api/foo")


async def test_session_api_post_timeout(logger, client):
    def post_timeout_error(connection, **kwargs):
        timeout_error(connection, timeout=kwargs.get("timeout"))

    client.post = CoroutineMock(side_effect=post_timeout_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)

    with pytest.raises(error.TimeoutError):
        await api_session.async_api_post("/api/foo", {})


async def test_session_api_get_client_error(logger, client):
    client.get = CoroutineMock(side_effect=client_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.ClientError):
        await api_session.async_api_get("/api/foo")


async def test_session_api_post_client_error(logger, client):
    def post_client_error(connection, **kwargs):
        client_error(connection, timeout=kwargs.get("timeout"))

    client.post = CoroutineMock(side_effect=post_client_error)
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.ClientError):
        await api_session.async_api_post("/api/foo", {})


async def test_session_api_get_http_error(logger, client):
    client.get = CoroutineMock(return_value=bad_http_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.HttpError):
        await api_session.async_api_get("/api/foo")


async def test_session_api_post_http_error(logger, client):
    client.post = CoroutineMock(return_value=bad_http_response())
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    with pytest.raises(error.HttpError):
        await api_session.async_api_post("/api/foo", {})


async def test_session_provides_a_logger(logger, client):
    api_session = Session("127.0.0.4", "88", 2, client, None, logger)
    api_session.logger.debug("foobar")
    logger.debug.assert_called_once_with("foobar")
