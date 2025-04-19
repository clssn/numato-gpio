"""Fixtures commonly used by tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from serialmock import SerialMockBase, serialmock

import numato_gpio
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
