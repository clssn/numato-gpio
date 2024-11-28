"""Fixtures commonly used by tests."""

import pytest
import serial
import serialmock

# ruff: noqa: ANN001,INP001,S101


@pytest.fixture
def mock_device(monkeypatch) -> None:
    """Mock the serial.Serial class with our serialmock.SerialMock."""
    monkeypatch.setattr(serial, "Serial", serialmock.SerialMock)
