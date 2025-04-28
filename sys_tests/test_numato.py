"""System tests, using a real numato device."""

import pytest

import numato_gpio as gpio

# ruff: noqa: ANN001,INP001,S101


@pytest.fixture(name="dev")
def dev_fixture() -> gpio.NumatoUsbGpio:
    """Fixture to acquire a numato device to be used by tests."""
    gpio.discover()
    return next(iter(gpio.devices.values()))


def test_nothing_discovered() -> None:
    """Device list shall be empty after discovery against a non-existing device file."""
    gpio.discover(["/dev/__notexisting__"])
    assert not gpio.devices


def test_write(dev: gpio.NumatoUsbGpio) -> None:
    """Port setup and write to a particular port shall not fail."""
    for port in range(dev.spec.ports):
        dev.setup(port, direction=gpio.Direction.OUT)
        dev.write(port, value=1)
        dev.write(port, value=0)


def test_read(dev: gpio.NumatoUsbGpio) -> None:
    """Port setup and readign from a particular port shall not fail."""
    for port in range(dev.spec.ports):
        dev.setup(port, direction=gpio.Direction.IN)
        assert dev.read(port) is not None


def test_adc_read(dev: gpio.NumatoUsbGpio) -> None:
    """Port setup and read from ADC port shall be in ADC range 0-1023."""
    for port in dev.spec.adc_ports:
        dev.setup(port, direction=gpio.Direction.IN)
        assert dev.adc_read(port) in range(2**dev.spec.adc_resolution_bits)


def test_cleanup() -> None:
    """Cleanup shall not leave any devices in the list."""
    gpio.cleanup()
    assert not gpio.devices
