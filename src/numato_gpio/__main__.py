"""Main module printing detected numato devices on the command-line."""

from importlib.metadata import version

import rich

from numato_gpio import cleanup, devices, discover


def main() -> None:
    """Print out information about all discovered devices."""
    try:
        rich.print(f"[dim]numato-gpio v{version('numato-gpio')}[/dim]\n")
        discover()
        rich.print(
            f"[bold]Discovered devices: [/bold]{'(None)' if not devices else ''}"
        )
        for device in devices.values():
            rich.print(device)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
