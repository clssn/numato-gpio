import numato_gpio
import pytest

from common import PORTS, Position


@pytest.mark.parametrize("ports", PORTS)
def test_instatiate_cleanup(ports, mock_device, monkeypatch):
    """Test the initialization of a device instance against a mockup."""
    monkeypatch.setattr("serial.Serial.ports", ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    dev.cleanup()


def test_write(mock_device, monkeypatch):
    monkeypatch.setattr("serial.Serial.ports", 128)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    for p in range(128):
        with pytest.raises(numato_gpio.NumatoGpioError):
            dev.write(p, 0)

    dev.iodir = 0  # all outputs
    for p in range(128):
        dev.write(p, 0)


def test_notify(mock_device, monkeypatch):
    monkeypatch.setattr("serial.Serial.ports", 128)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    dev.notify = True
