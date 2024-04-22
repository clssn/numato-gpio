import asyncio
from pathlib import Path
from typing import List, Optional
import rich
import typer
from typing_extensions import Annotated
import numato_gpio
from numato_gpio.cli import utils


async def list_devices() -> List[str]:
    return [str(p) for p in Path("/dev").iterdir()]


app = typer.Typer()


@utils.asyncio_run
async def discover(
    verbose: Annotated[bool, typer.Option("--verbose", help="Verbose output")] = False,
    devices: Annotated[
        Optional[List[str]],
        typer.Option(
            "--device",
            "-d",
            metavar="DEVICE",
            help="Device file path, option can be used multiple times",
            show_default=True,
            autocompletion=utils.async_completion(list_devices),
        ),
    ] = numato_gpio.DEFAULT_DEVICES,
):
    """Print information about all discovered Numato GPIO devices."""
    try:
        if verbose:
            rich.print("[bold]Scanning devices:[/bold]\n")
            rich.print("\n".join(dev for dev in devices))
            rich.print()

        await asyncio.get_event_loop().run_in_executor(None, numato_gpio.discover)

        rich.print(
            f"[bold]Discovered devices[/bold]: {'(None)' if not numato_gpio.devices else ''}"
        )
        rich.print()
        for device in numato_gpio.devices.values():
            rich.print(device)
    finally:
        await asyncio.get_event_loop().run_in_executor(None, numato_gpio.cleanup)


app.command()(discover)

if __name__ == "__main__":
    app()
