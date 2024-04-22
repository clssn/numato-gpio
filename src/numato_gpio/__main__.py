"""Main module printing detected numato devices on the command-line."""

import asyncio
from pathlib import Path
from typing import List, Optional

import rich
import typer
from numato_gpio.cli import cmd_numato
from typing_extensions import Annotated

import numato_gpio
from numato_gpio.cli import cmd_numato

main = cmd_numato.app

if __name__ == "__main__":
    main()

