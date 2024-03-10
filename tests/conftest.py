import pytest
import serial
import serialmock


@pytest.fixture()
def mock_device(monkeypatch):
    """Mock the serial.Serial class with our serialmock.SerialMock."""
    monkeypatch.setattr(serial, "Serial", serialmock.gen_serial())
