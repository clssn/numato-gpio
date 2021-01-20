import pytest
import serial
import serialmock


@pytest.fixture(params=["\r\n", "\n\r", "\r", "\n"], ids=["crlf", "lfcr", "cr", "lf"])
def mock_device(monkeypatch, request):
    """Mock the serial.Serial class with our serialmock.SerialMock.

    Parametrized different response-line endings model the different line
    endings different numato devices respond with, even with the same firmware
    version.

    Note:
        cr = carriage return = "\r"
        lf = line feed = "\n"

    """
    monkeypatch.setattr(serial, "Serial", serialmock.gen_serial(request.param))
