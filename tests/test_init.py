"""Test device initialization agains mockup devices."""

import pytest

import numato_gpio
from numato_gpio.device_types import DeviceType

# ruff: noqa: ANN001,INP001,S101


@pytest.mark.usefixtures("mock_device")
@pytest.mark.parametrize("device_type", set(DeviceType))
def test_instatiate_cleanup(device_type: DeviceType, monkeypatch) -> None:
    """A numato device mockup shall be initializable and properly cleaned up.

    This shall be possible for devices of any number of ports and not raise.
    """
    monkeypatch.setattr("serial.Serial.ports", device_type.value.ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    dev.cleanup()


@pytest.mark.usefixtures("mock_device")
def test_write(monkeypatch) -> None:
    """A numato device mockup shall raise if input ports are written to.

    This is only tested on a 128 bit mockup device.
    """
    monkeypatch.setattr("serial.Serial.ports", 128)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    for p in range(128):
        with pytest.raises(numato_gpio.NumatoIoDirError, match=f"port #{p}"):
            dev.write(p, value=0)

    dev.iodir = 0  # all outputs
    for p in range(128):
        dev.write(p, value=0)


@pytest.mark.usefixtures("mock_device")
@pytest.mark.parametrize("device_type", set(DeviceType))
def test_notify(monkeypatch, device_type: DeviceType) -> None:
    """Notification setup success shall depend on device's notifications support.

    NumatoGpioError shall be raised when trying to use any notification API.
    """
    monkeypatch.setattr("serial.Serial.ports", device_type.value.ports)
    dev = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    if dev.spec.supports_notification:
        dev.notify = True
    else:
        with pytest.raises(numato_gpio.NumatoNotifyNotSupportedError):
            dev.notify = True
