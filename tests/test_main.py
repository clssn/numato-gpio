"""Test the main function."""

import os
from unittest import mock

import pytest

import numato_gpio
from numato_gpio.device_types import DeviceType

# ruff: noqa: ANN001,INP001,S101


@pytest.mark.parametrize("device_type", set(DeviceType))
@pytest.mark.usefixtures("mock_device")
def test_main(device_type: DeviceType, monkeypatch, capsys) -> None:
    """Ensure main lists available devices."""
    with mock.patch.object(numato_gpio.discover, "__defaults__", (["/dev/ttyACMxx"],)):
        monkeypatch.setattr("serial.Serial.ports", device_type.value.ports)
        from numato_gpio.__main__ import main

        main()
        cap = capsys.readouterr()
        assert cap.out.startswith("numato-gpio")
        assert f"Discovered devices: {os.linesep}dev: /dev/ttyACMxx" in cap.out
        assert cap.err == ""
