"""Fixtures commonly used by tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from serialmock import SerialMockBase, serialmock
from serialmock_async import create_async_serial_mock_factory

import numato_gpio
from numato_gpio.async_api import NumatoUsbGpioAsync
from numato_gpio.device_types import DeviceType

# ruff: noqa: ANN001,INP001,S101


@pytest.fixture(params=DeviceType)
def mock_serial(
    request,
) -> Generator[type[SerialMockBase], Any, Any]:
    """Patch a serial mockup for any supported device."""
    device_type = request.param
    with patch("numato_gpio.serial.Serial", new=serialmock(device_type)) as serial_mock:
        yield serial_mock


@pytest.fixture
def mock_gpio(mock_serial) -> numato_gpio.NumatoUsbGpio:  # noqa: ARG001
    """Initialize a NumatoUsbGpio object for any supported device."""
    return numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")


# Async fixtures


@pytest.fixture(params=DeviceType)
def mock_serial_async(request):
    """Patch an async serial mockup for any supported device."""
    device_type = request.param
    mock_factory = create_async_serial_mock_factory(device_type)
    with patch(
        "numato_gpio.async_api.serial_asyncio.open_serial_connection",
        new=mock_factory,
    ) as serial_mock:
        yield serial_mock, device_type


@pytest.fixture
async def mock_gpio_async(mock_serial_async) -> NumatoUsbGpioAsync:  # noqa: ARG001
    """Initialize a NumatoUsbGpioAsync object for any supported device."""
    device = await NumatoUsbGpioAsync.create("/dev/ttyACMxx")
    yield device
    # Cleanup
    try:
        await device.cleanup()
    except Exception:  # noqa: S110
        pass  # Ignore cleanup errors in tests
