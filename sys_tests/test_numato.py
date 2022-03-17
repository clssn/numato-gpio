import numato_gpio as gpio
from pytest import fixture


@fixture
def dev():
    return list(gpio.devices.values())[0]


def test_nothing_discovered():
    gpio.discover(["/dev/__notexisting__"])
    assert not gpio.devices


def test_regular_discover_return_none_device_found():
    assert gpio.discover(["/dev/ttyACM0"]) is None
    assert gpio.devices


def test_write(dev):
    dev.setup(4, gpio.OUT)
    dev.write(4, 1)


def test_read(dev):
    dev.setup(27, gpio.IN)
    assert dev.read(27) is not None


def test_adc_read(dev):
    dev.setup(2, gpio.IN)
    assert dev.adc_read(2) in range(1024)


def test_cleanup():
    gpio.cleanup()
