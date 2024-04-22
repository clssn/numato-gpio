import rich
import typer
from typing_extensions import Annotated

from numato_gpio.cli import utils

app = typer.Typer()


def ver(device: Annotated[int, utils.numato_device_option]):
    """Print the version of a device."""
    rich.print(device.ver)


app.command()(ver)
