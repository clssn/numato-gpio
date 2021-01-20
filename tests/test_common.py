import numato_gpio
import pytest

@pytest.mark.parametrize("ports", [8, 16, 32, 64, 128])
def test_instatiate(ports, mock_device, monkeypatch):
    """Test the initialization of a device instance against a mockup."""
    monkeypatch.setattr("serial.Serial.ports", ports)
    inst = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    inst.cleanup()
