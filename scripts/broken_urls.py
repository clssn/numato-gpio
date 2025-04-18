"""Find broken device documentation URLs.

Print broken URLs line by line and terminate with error code (1) if any are found.
"""

import sys
from enum import Enum

import requests

from numato_gpio.device_types import DeviceType


class ExitCode(Enum):
    """Command-line style exit codes."""

    success = 0
    error = 1


def main() -> int:
    """Print broken URLs line by line.

    Return error (1) if any are found.
    """
    print(  # noqa: T201
        "\n".join(
            broken := [
                d.value.url
                for d in DeviceType
                if not requests.get(d.value.url, timeout=2).ok
            ]
        ),
        file=sys.stderr,
    )
    sys.exit(ExitCode.error.value if broken else ExitCode.success.value)


if __name__ == "__main__":
    main()
