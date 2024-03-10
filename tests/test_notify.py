"""This module shall ensure that notifications are correctly handled anywhere in the input stream."""

from unittest.mock import Mock

import pytest
from common import PORTS, Position

import numato_gpio


@pytest.mark.parametrize("ports", PORTS)
@pytest.mark.parametrize(
    "position",
    [
        Position.FRONT,
        Position.CENTER,
        Position.BACK,
    ],
)
@pytest.mark.usefixtures("mock_device")
def test_notify(ports, position, monkeypatch):
    """Test notifications."""
    monkeypatch.setattr("serial.Serial.ports", ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")

    # expect devices that don't support notifications to raise (but still proceed with tests)
    if not dev.can_notify:
        with pytest.raises(numato_gpio.NumatoGpioError):
            dev.notify = True
    else:
        dev.notify = True

    msg = b"gpio readall\r"
    # Need the particular Serial (mock) instance created in the constructor of NumatoUsbGpio
    serial_mock = dev._ser  # pylint: disable=protected-access
    msg_length = len(msg) - len("\r") + len(serial_mock.eol) * 2 + ports // 4
    if position == Position.FRONT:
        monkeypatch.setattr(serial_mock, "notify_inject_at", 0)
    elif position == Position.CENTER:
        monkeypatch.setattr(serial_mock, "notify_inject_at", msg_length // 2)
    elif position == Position.BACK:
        monkeypatch.setattr(serial_mock, "notify_inject_at", msg_length)

    port_callbacks = []
    for p in range(ports):
        cb = Mock()
        dev.setup(p, numato_gpio.IN)
        if dev.can_notify:
            dev.add_event_detect(p, cb, numato_gpio.BOTH)
        else:
            with pytest.raises(numato_gpio.NumatoGpioError):
                dev.add_event_detect(p, cb, numato_gpio.BOTH)
        port_callbacks.append(cb)
    dev.readall()
    if dev.can_notify:
        assert all(cb.called_with(p, True) for cb in port_callbacks)
    else:
        assert not any(cb.called for cb in port_callbacks)
    dev.cleanup()
