"""System tests, using a real numato device."""

import pytest

import numato_gpio as gpio

# ruff: noqa: ANN001,INP001,S101


@pytest.fixture(name="dev")
@pytest.mark.serial
def dev_fixture() -> None:
    """Fixture to acquire a numato device to be used by tests."""
    gpio.discover()
    return next(iter(gpio.devices.values()))


def test_nothing_discovered() -> None:
    """Device list shall be empty after discovery against a non-existing device file."""
    gpio.discover(["/dev/__notexisting__"])
    assert not gpio.devices


def test_write(dev: gpio.NumatoUsbGpio) -> None:
    """Port setup and write to a particular port shall not fail."""
    dev.setup(4, direction=gpio.Direction.OUT)
    dev.write(4, value=1)


def test_read(dev: gpio.NumatoUsbGpio) -> None:
    """Port setup and readign from a particular port shall not fail."""
    dev.setup(27, direction=gpio.Direction.IN)
    assert dev.read(27) is not None


def test_adc_read(dev: gpio.NumatoUsbGpio) -> None:
    """Port setup and read from ADC port shall be in ADC range 0-1023."""
    dev.setup(2, direction=gpio.Direction.IN)
    assert dev.adc_read(2) in range(1024)


def test_cleanup() -> None:
    """Cleanup shall not leave any devices in the list."""
    gpio.cleanup()
    assert not gpio.devices
