"""Main module printing detected numato devices on the command-line."""

import importlib.metadata
from numato_gpio import cleanup, devices, discover


def main():
    """Print out information about all discovered devices."""
    try:
        discover()
        print(f"Discovered devices: {'(None)' if not devices else ''}")
        print(f"\nnumato-gpio v{importlib.metadata.version('numato-gpio')}")
        for device in devices.values():
            print(device)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
