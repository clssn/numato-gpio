"""Test the main function."""

import os
from unittest import mock

import pytest

import numato_gpio

# ruff: noqa: ANN001,INP001,S101


@pytest.mark.usefixtures("mock_serial")
def test_main(capsys) -> None:
    """Ensure main lists available devices."""
    with mock.patch.object(numato_gpio.discover, "__defaults__", (["/dev/ttyACMxx"],)):
        from numato_gpio.__main__ import main

        main()
        cap = capsys.readouterr()
        assert cap.out.startswith("numato-gpio")
        assert f"Discovered devices: {os.linesep}dev: /dev/ttyACMxx" in cap.out
        assert cap.err == ""
