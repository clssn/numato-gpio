import functools
from pathlib import Path
from typing import List

import anyio
import click
import typer

import numato_gpio


def asyncio_run(func):
    """Decorator to run a function in an async context."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        async def coro_wrapper():
            return await func(*args, **kwargs)

        return anyio.run(coro_wrapper)

    return wrapper


def async_completion(func):
    """Wrapper to pass a coroutine as an autocompletion function."""
    func = asyncio_run(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (click.exceptions.Abort, click.exceptions.Exit):
            return []

    return wrapper


def _device_by_id_or_file(device_specifier: int | str) -> numato_gpio.NumatoUsbGpio:
    """Find a NumatoUsbGpio device by id."""
    if Path(device_specifier).is_char_device():
        return numato_gpio.NumatoUsbGpio(device_specifier)

    numato_gpio.discover()
    try:
        return numato_gpio.devices[int(device_specifier)]
    except KeyError as err:
        raise click.ClickException(
            f"Device with id {device_specifier} not found."
        ) from err
    except ValueError as err:
        raise click.ClickException(
            f"Device specifier {device_specifier} must be a positive integer."
        ) from err


def _autocomplete_devices(incomplete: str) -> List[str]:
    if incomplete.startswith("/"):
        return [
            str(p)
            for p in Path("/dev").iterdir()
            if str(p).startswith(incomplete) and str(p).startswith("/dev/ttyACM")
        ]
    numato_gpio.discover()
    return (
        [
            f"{k}"
            for k, _ in numato_gpio.devices.items()
            if str(k).startswith(incomplete)
        ]
        if numato_gpio.devices
        else []
    )


numato_device_option = typer.Option(
    "--device",
    "-d",
    help="The Numato device specified via its id or the OS's device file.",
    parser=_device_by_id_or_file,
    metavar="DEVICE",
    autocompletion=_autocomplete_devices,
    show_default=False,
)


def validate_port_range(ctx, _param, value):
    """Ensure a valid port number, otherwise raise a ClickException."""
    device = ctx.params.get("device")
    if value < 0 or value >= device.ports:
        raise click.ClickException(
            f"Port number {value} out of range (0-{device.ports})."
        )
    return value
