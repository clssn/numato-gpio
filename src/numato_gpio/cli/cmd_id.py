import asyncio
from pathlib import Path
from typing import List, Optional

import rich
import typer
from typing_extensions import Annotated

import numato_gpio
from numato_gpio.cli import utils

app = typer.Typer(
    help="Manage device IDs.",
    no_args_is_help=True,
)


@app.command()
@utils.asyncio_run
async def get(
        device: Annotated[numato_gpio.NumatoUsbGpio, utils.numato_device_option],
):
    """Print the device ID."""
    rich.print(device.id)


@app.command(name="set")
@utils.asyncio_run
async def set_(
        device: Annotated[numato_gpio.NumatoUsbGpio, utils.numato_device_option],
        id_: Annotated[int, typer.Argument(hidden=True, show_default=False, metavar="ID")],
):
    """Write an ID to the device."""
    old_id = device.id
    if old_id == id_:
        rich.print(f"Warning: Re-writing same ID {id_} to device. ID will be unchanged.")
    device.id=id_
    rich.print(f"Device {old_id} now has ID {id_}")
