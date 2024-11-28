"""System tests, using a real numato device."""

from pytest import fixture

import numato_gpio as gpio


@fixture(name="dev")
def dev_fixture():
    """Fixture to acquire a numato device to be used by tests."""
    gpio.discover()
    return list(gpio.devices.values())[0]


def test_nothing_discovered():
    """Device list shall be empty after discovery against a non-existing device file."""
    gpio.discover(["/dev/__notexisting__"])
    assert not gpio.devices


def test_write(dev):
    """Port setup and write to a particular port shall not fail."""
    dev.setup(4, gpio.OUT)
    dev.write(4, 1)


def test_read(dev):
    """Port setup and readign from a particular port shall not fail."""
    dev.setup(27, gpio.IN)
    assert dev.read(27) is not None


def test_adc_read(dev):
    """Port setup and read from ADC port shall be in ADC range 0-1023."""
    dev.setup(2, gpio.IN)
    assert dev.adc_read(2) in range(1024)


def test_cleanup():
    """Cleanup shall not leave any devices in the list."""
    gpio.cleanup()
    assert not gpio.devices
