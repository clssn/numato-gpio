import numato_gpio


def test_instatiate(mock_device):
    """Test the initialization of a device instance against a mockup."""
    inst = numato_gpio.NumatoUsbGpio("/dev/ttyACMxx")
    inst.cleanup()
