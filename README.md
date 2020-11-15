![Upload Python Package](https://github.com/clssn/numato-gpio/workflows/Upload%20Python%20Package/badge.svg)

# Python API for Numato GPIO Expanders

This Python API can be used to control [Numato 32 Port USB
GPIO](https://numato.com/product/32-channel-usb-gpio-module-with-analog-inputs)
expanders.

* Configure ports as input or output port
* Write to output ports
* Read from input ports
* Read integer values from ADC input ports (1 - 7)
* Register a callback for input port events (edge detection)

See the [changelog](changelog.md) for details on the releases.

## Installation

Install latest development version:

    pip install --user git+https://github.com/clssn/numato-gpio.git

Install latest release:

    pip install --user numato-gpio

## Usage CLI

Test whether your devices can be found running the command-line interface like
`python3 -m numato_gpio`. Remember to have your user in the `dialout` group,
since the devices are registered as /dev/ttyACMx (i.e. modem devices).

Expected output:

```
❯ python3 -m numato_gpio
dev: /dev/ttyACM0 | id: 0 | ver: 9 | iodir: 0xffffffff | iomask: 0x00000000 | state: 0x00000000
dev: /dev/ttyACM1 | id: 1 | ver: 9 | iodir: 0xffffffff | iomask: 0x00000000 | state: 0x00000000
```

## Usage API

The API can be used like:

```python
import numato_gpio as gpio

my_device_id = 0
gpio.discover()
dev = gpio.devices[my_device_id]

# configure port 4 as output and set it to high
dev.setup(4, gpio.OUT)
dev.write(4, 1)

# configure port 27 as input and print its logic level
dev.setup(27, gpio.IN)
print(dev.read(27))

# configure port 2 as input and print its ADC value
dev.setup(2, gpio.IN)
print(dev.adc_read(2))

# configure port 14 as input and setup notification on logic level changes
dev.setup(14, gpio.IN)
def callback(port, level):
    print("{edge:7s} edge detected on port {port} "
        "-> new logic level is {level}".format(
        edge="Rising" if level else "Falling",
        port=port,
        level="high" if level else "low")
    )

dev.add_event_detect(14, callback, gpio.BOTH)
dev.notify = True
```
## Versions

See [changelog](changelog.md).

## Known Issues

Though the code works well in a [Home Assistant](https://home-assistant.io)
integration since 2018, there are quite some aspects to improve. The following
issues are only the ones the author is aware of:

* No unit tests
* Some docstrings are hard to understand
* Device discovery/registry as module-global dict is sub-optimal
* Only `/dev/ACMx` devices are scanned which were mapped on the author's Linux
