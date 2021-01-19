import pytest
import serial
import serialmock


@pytest.fixture(params=["\r\n", "\n\r", "\r", "\n"])
def mock_device(monkeypatch, request):
    """Mock the serial.Serial class with our serialmock.SerialMock.

    Parametrized different response-line endings model the different line
    endings different numato devices respond with, even with the same firmware
    version.
    """
    monkeypatch.setattr(serial, "Serial", serialmock.gen_serial(request.param))
