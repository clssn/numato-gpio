from unittest.mock import Mock

import numato_gpio
import pytest

from common import PORTS, Position


@pytest.mark.parametrize("ports", PORTS)
@pytest.mark.parametrize("position", [
    Position.FRONT,
    Position.CENTER,
    Position.BACK,
])
def test_notify(ports, position, mock_device, monkeypatch):
    """Test notifications."""
    monkeypatch.setattr("serial.Serial.ports", ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    dev.notify = True
    msg = b"gpio readall\r"
    l = len(msg) - len("\r") + len(dev._ser.eol) * 2 + ports // 4
    if position == Position.FRONT:
        monkeypatch.setattr(dev._ser, "notify_inject_at", 0)
    elif position == Position.CENTER:
        monkeypatch.setattr(dev._ser, "notify_inject_at", l // 2)
    elif position == Position.BACK:
        monkeypatch.setattr(dev._ser, "notify_inject_at", l)

    callbacks = []
    if ports != 8:
        for p in range(ports):
            cb = Mock()
            dev.setup(p, numato_gpio.IN)
            dev.add_event_detect(p, cb, numato_gpio.BOTH)
            callbacks.append(cb)
    dev.readall()
    if ports != 8:
        for p in range(ports):
            callbacks[p].assert_called_with(p, True)
    dev.cleanup()
