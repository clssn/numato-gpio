"""Test device initialization agains mockup devices."""

import pytest
from common import PORTS

import numato_gpio


@pytest.mark.usefixtures("mock_device")
@pytest.mark.parametrize("ports", PORTS)
def test_instatiate_cleanup(ports, monkeypatch):
    """A numato device mockup shall be initializable and properly cleaned up.

    This shall be possible for devices of any number of ports and not raise.
    """
    monkeypatch.setattr("serial.Serial.ports", ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    dev.cleanup()


@pytest.mark.usefixtures("mock_device")
def test_write(monkeypatch):
    """A numato device mockup shall raise if input ports are written to.

    This is only tested on a 128 bit mockup device.
    """
    monkeypatch.setattr("serial.Serial.ports", 128)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    for p in range(128):
        with pytest.raises(numato_gpio.NumatoGpioError):
            dev.write(p, 0)

    dev.iodir = 0  # all outputs
    for p in range(128):
        dev.write(p, 0)


@pytest.mark.usefixtures("mock_device")
@pytest.mark.parametrize("ports", PORTS)
def test_notify(monkeypatch, ports):
    """Notification setup success shall depend on device's notifications support.

    NumatoGpioError shall be raised when trying to use any notification API.
    """
    monkeypatch.setattr("serial.Serial.ports", ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    if dev.can_notify:
        dev.notify = True
    else:
        with pytest.raises(numato_gpio.NumatoGpioError):
            dev.notify = True
