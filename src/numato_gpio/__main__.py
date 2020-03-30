"""Main module printing detected numato devices on the command-line."""
from numato_gpio import discover, cleanup, devices


def main():
    """Print out information about all discovered devices."""
    try:
        discover()
        for device in devices.values():
            print(device)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
