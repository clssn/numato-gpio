"""Ensure that notifications are correctly handled anywhere in the input stream."""

from enum import Enum
from unittest.mock import Mock

import pytest

import numato_gpio
from numato_gpio.device_types import DeviceType


# ruff: noqa: ANN001,INP001,S101
class Position(Enum):
    """Position to generate a notification."""

    FRONT = 1
    CENTER = 2
    BACK = 3


@pytest.mark.parametrize("device_type", set(DeviceType))
@pytest.mark.parametrize(
    "position",
    [
        Position.FRONT,
        Position.CENTER,
        Position.BACK,
    ],
)
@pytest.mark.usefixtures("mock_device")
def test_notify(device_type: DeviceType, position: int, monkeypatch) -> None:
    """Test notifications."""
    monkeypatch.setattr("serial.Serial.ports", device_type.value.ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")

    if not dev.spec.supports_notification:
        with pytest.raises(numato_gpio.NumatoNotifyNotSupportedError):
            dev.notify = True
    else:
        dev.notify = True

    msg = b"gpio readall\r"
    # Need the particular Serial (mock) instance created in NumatoUsbGpio constructor
    serial_mock = dev._ser  # pylint: disable=protected-access  # noqa: SLF001
    msg_length = (
        len(msg) - len("\r") + len(serial_mock.eol) * 2 + device_type.value.ports // 4
    )
    if position == Position.FRONT:
        monkeypatch.setattr(serial_mock, "notify_inject_at", 0)
    elif position == Position.CENTER:
        monkeypatch.setattr(serial_mock, "notify_inject_at", msg_length // 2)
    elif position == Position.BACK:
        monkeypatch.setattr(serial_mock, "notify_inject_at", msg_length)

    port_callbacks = []
    for p in range(device_type.value.ports):
        cb = Mock()
        dev.setup(p, direction=numato_gpio.Direction.IN)
        if dev.spec.supports_notification:
            dev.add_event_detect(p, cb, numato_gpio.Edge.BOTH)
        else:
            with pytest.raises(numato_gpio.NumatoNotifyNotSupportedError):
                dev.add_event_detect(p, cb, numato_gpio.Edge.BOTH)
        port_callbacks.append(cb)
    dev.readall()
    if dev.spec.supports_notification:
        for p, cb in enumerate(port_callbacks):
            cb.assert_called_with(p, True)  # noqa: FBT003
    else:
        assert not any(cb.called for cb in port_callbacks)
    dev.cleanup()
