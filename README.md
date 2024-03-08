![Upload Python Package](https://github.com/clssn/numato-gpio/workflows/Upload%20Python%20Package/badge.svg)
![Tests](https://github.com/clssn/numato-gpio/workflows/Tests/badge.svg)

# Python API for Numato GPIO Expanders

This Python API can be used to control [Numato USB
GPIO expanders](https://numato.com/product/32-channel-usb-gpio-module-with-analog-inputs).

* Configure ports as input or output port
* Write to output ports
* Read from input ports
* Read integer values from ADC input ports (1 - 7)
* Register a callback for input port events (edge detection)

See the [changelog](changelog.md) for details on the releases.

## Installation using pipx

Install pipx if you don't have it. It isolates your python tools' dependencies.

    pip install pipx
    pipx ensurepath  # helps the shell to find the tools by adding ~/.local/bin to the path

Install latest development version:

    pipx install git+https://github.com/clssn/numato-gpio.git

Or install latest release:

    pipx install numato-gpio

## Usage CLI

Test whether your devices can be found running the command-line interface like
`numato-discover`. Remember to have your user in the `dialout` group,
since the devices are registered as /dev/ttyACMx (i.e. modem devices).

Expected output:

```
❯ python3 -m numato_gpio
dev: /dev/ttyACM0 | id: 0 | ver: 00000009 | ports: 32 | iodir: 0xffffffff | iomask: 0x00000000 | state: 0x00000000
dev: /dev/ttyACM1 | id: 1 | ver: 00000009 | ports: 32 | iodir: 0xffffffff | iomask: 0x00000000 | state: 0x00000000
```

## Usage API

The API can be used like:

```python
import numato_gpio as gpio

# You can instantiate the device directly from its OS identifier, for instance
# "/dev/ttyACM0" on Linux or "COM5" on Windows.
dev = gpio.NumatoUsbGpio("/dev/ttyACM0")

# Alternatively, you can use the discovery function, but it is limited to
# Linux' /dev/ttyACM* devices. This is because discovery will open and try to
# interact with any device. This can lead to errors in unrelated devices.
# Under windows the naming scheme is entirely flat (COMx) increasing the error
# potential, so no discovery here.
# my_device_id = 0
# gpio.discover()
# dev = gpio.devices[my_device_id]

# Configure port 4 as output and set it to high
dev.setup(4, gpio.OUT)
dev.write(4, 1)

# Configure port 27 as input and print its logic level
dev.setup(27, gpio.IN)
print(dev.read(27))

# Configure port 2 as input and print its ADC value
dev.setup(2, gpio.IN)
print(dev.adc_read(2))

# Configure port 14 as input and setup notification on logic level changes
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
## Release Versions

See [changelog](changelog.md).

## Troubleshooting

In case your device can't be discovered or you even get an error message or
stacktrace, please follow the [troubleshooting guide](doc/troubleshooting.md).

## Known Issues

Though the code works well in a [Home Assistant](https://home-assistant.io)
integration since 2018, there are quite some aspects to improve. The following
issues are only the ones the author is aware of:

* Some docstrings are hard to understand
* Device discovery/registry as module-global dict is sub-optimal
* Only `/dev/ACMx` devices are scanned which were mapped on the author's Linux
* No async API available

## Install development environment

If you plan to make a contribution you should use `poetry` to set-up your
development environment. So first make sure to install the tool if you don't
have it already.

    pip install poetry

Then have poetry install the dependencies and the numato-project (editable) in a
virtualenv.

    poetry install

You can now activate the virtualenv (.venv directory) like

    poetry shell

If you use VSCode or similar IDEs, ensure that their Python environment is
configured to the .venv directory so their tools, like Debugger, Test Explorer
etc., work.

Note that all commands of the Makefile are using `poetry run`, so you don't have
to run `poetry shell` before calling them.

## System Tests

Unit tests in the `tests` directory are using a device mockup which mimicks
a Numato device's responses as far as known at the state of development.

System tests in the `sys_tests` folder are meant to be run using a real device
and will just fail, if no device is connected. They are an important complement
to unit tests, because they are *the real thing* and might behave differently
than the mockup device for the unit tests.

If you consider to run system tests you should be aware that it may be dangerous
running them.

---
**WARNING**

Only run the system tests with *gpio ports disconnected*! You otherwise risk
a short circuit which may lead to damage or destruction of your device or worse.
---
