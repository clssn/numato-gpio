"""Test device initialization against mockup devices."""

import pytest

import numato_gpio

# ruff: noqa: ANN001,INP001,S101


def test_instatiate_cleanup(mock_gpio: numato_gpio.NumatoUsbGpio) -> None:
    """A numato device mockup shall be initializable and properly cleaned up.

    This shall be possible for devices of any number of ports and not raise.
    """
    mock_gpio.cleanup()


def test_write(mock_gpio: numato_gpio.NumatoUsbGpio) -> None:
    """A numato device mockup shall raise if input ports are written to."""
    for p in range(mock_gpio.spec.ports):
        with pytest.raises(numato_gpio.NumatoIoDirError, match=f"port #{p}"):
            mock_gpio.write(p, value=0)

    mock_gpio.iodir = 0  # all outputs
    for p in range(mock_gpio.spec.ports):
        mock_gpio.write(p, value=0)


def test_notify(mock_gpio: numato_gpio.NumatoUsbGpio) -> None:
    """Notification setup success shall depend on device's notifications support.

    NumatoGpioError shall be raised when trying to use any notification API.
    """
    if mock_gpio.spec.supports_notification:
        mock_gpio.notify = True
    else:
        with pytest.raises(numato_gpio.NumatoNotifyNotSupportedError):
            mock_gpio.notify = True
