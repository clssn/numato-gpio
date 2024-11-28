"""Main module printing detected numato devices on the command-line."""

from numato_gpio import cleanup, devices, discover


def main() -> None:
    """Print out information about all discovered devices."""
    try:
        discover()
        print(f"Discovered devices: {'(None)' if not devices else ''}")  # noqa: T201
        for device in devices.values():
            print(device)  # noqa: T201
    finally:
        cleanup()


if __name__ == "__main__":
    main()
