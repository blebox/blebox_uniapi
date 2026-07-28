"""Tests for the Update feature."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from blebox_uniapi.update import Update
from blebox_uniapi import error


@pytest.fixture
def mock_product():
    product = MagicMock()
    product.firmware_version = "0.176"
    product.available_firmware_version = None
    return product


@pytest.fixture
def update(mock_product):
    return Update(mock_product, "update", {})


class TestInstalledVersion:
    def test_returns_firmware_version(self, update, mock_product):
        assert update.installed_version == "0.176"

    def test_returns_none_when_not_set(self, update, mock_product):
        mock_product.firmware_version = None
        assert update.installed_version is None


class TestLatestVersion:
    def test_returns_none_when_not_set(self, update, mock_product):
        assert update.latest_version is None

    def test_returns_available_firmware_version(self, update, mock_product):
        mock_product.available_firmware_version = "1.2.3"
        assert update.latest_version == "1.2.3"


class TestAsyncUpdate:
    async def test_calls_ota_check_on_product(self, update, mock_product):
        mock_product.async_ota_check = AsyncMock()
        await update.async_update()
        mock_product.async_ota_check.assert_called_once()

    async def test_propagates_connection_error_from_ota_check(
        self, update, mock_product
    ):
        mock_product.async_ota_check = AsyncMock(
            side_effect=error.ConnectionError("connection refused")
        )
        with pytest.raises(error.ConnectionError):
            await update.async_update()


class TestAsyncInstall:
    async def test_calls_ota_update_on_product(self, update, mock_product):
        mock_product.async_ota_update = AsyncMock()
        await update.async_install()
        mock_product.async_ota_update.assert_called_once()

    async def test_propagates_connection_error_from_ota_update(
        self, update, mock_product
    ):
        mock_product.async_ota_update = AsyncMock(
            side_effect=error.ConnectionError("connection refused")
        )
        with pytest.raises(error.ConnectionError):
            await update.async_install()
