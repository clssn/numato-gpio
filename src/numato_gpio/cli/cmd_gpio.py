import typer
from typing_extensions import Annotated

import numato_gpio
from numato_gpio.cli import utils
import click

app = typer.Typer(
    help="Operate device IO and ADC ports.",
    no_args_is_help=True,
)

PORT_LOGIC_LEVEL_HIGH = 1
PORT_LOGIC_LEVEL_LOW = 0


@app.command(name="set")
def set_(
    device: Annotated[numato_gpio.NumatoUsbGpio, utils.numato_device_option],
    port: Annotated[
        int,
        typer.Argument(
            callback=utils.validate_port_range,
            show_default=False,
        ),
    ],
):
    """Turn a port on (high)."""
    try:
        device.write(port, PORT_LOGIC_LEVEL_HIGH)
    except numato_gpio.NumatoGpioError as err:
        raise click.ClickException("Failed to write to the device.") from err


@app.command()
def clear(
    device: Annotated[numato_gpio.NumatoUsbGpio, utils.numato_device_option],
    port: Annotated[
        int,
        typer.Argument(
            callback=utils.validate_port_range,
            show_default=False,
        ),
    ],
):
    """Turn a port off (low)."""
    try:
        device.write(port, PORT_LOGIC_LEVEL_LOW)
    except numato_gpio.NumatoGpioError as err:
        raise click.ClickException(f"Failed to write to the device.") from err


@app.command()
def read(
    device: Annotated[numato_gpio.NumatoUsbGpio, utils.numato_device_option],
    port: int,
):
    """Read port level."""
    try:
        print(device.read(port))
    except numato_gpio.NumatoGpioError as err:
        raise click.ClickException("Failed to write to the device.") from err


@app.command()
def iomask():
    """Configure the IO mask for all ports."""


@app.command()
def iodir():
    """Configure the IO direction for all ports."""


@app.command()
def readall():
    """Read all ports at once."""


@app.command()
def writeall():
    """Write all ports at once."""


app_notify = typer.Typer(help="Manage notifications.")
app.add_typer(app_notify, name="notify")


@app_notify.command()
def on():
    """Turn notifications on."""


@app_notify.command()
def off():
    """Turn notifications off."""


@app_notify.command()
def get():
    """Determine whether notifications are turned on or off."""
