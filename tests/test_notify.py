"""Ensure that notifications are correctly handled anywhere in the input stream."""

import time
from enum import Enum
from unittest.mock import Mock

import pytest

import numato_gpio


# ruff: noqa: ANN001,INP001,S101
class Position(Enum):
    """Position to generate a notification."""

    FRONT = 1
    CENTER = 2
    BACK = 3


@pytest.mark.parametrize(
    "position",
    [
        Position.FRONT,
        Position.CENTER,
        Position.BACK,
    ],
)
def test_notify(mock_gpio: numato_gpio.NumatoUsbGpio, position: Position) -> None:
    """Test notifications."""
    if not mock_gpio.spec.supports_notification:
        with pytest.raises(numato_gpio.NumatoNotifyNotSupportedError):
            mock_gpio.notify = True
    else:
        mock_gpio.notify = True

    msg = b"gpio readall\r"
    serial_mock = mock_gpio._ser  # noqa: SLF001
    msg_length = (
        len(msg) - len("\r") + len(serial_mock.eol) * 2 + mock_gpio.spec.ports // 4
    )
    if position == Position.FRONT:
        serial_mock.notify_inject_at = 0
    elif position == Position.CENTER:
        serial_mock.notify_inject_at = msg_length // 2
    elif position == Position.BACK:
        serial_mock.notify_inject_at = msg_length

    port_callbacks = []
    for p in range(mock_gpio.spec.ports):
        cb = Mock()
        mock_gpio.setup(p, direction=numato_gpio.Direction.IN)
        if mock_gpio.spec.supports_notification:
            mock_gpio.add_event_detect(p, cb, numato_gpio.Edge.BOTH)
        else:
            with pytest.raises(numato_gpio.NumatoNotifyNotSupportedError):
                mock_gpio.add_event_detect(p, cb, numato_gpio.Edge.BOTH)
        port_callbacks.append(cb)

    # query the device to provoke injection of notifications into the response
    mock_gpio.readall()

    if position == Position.BACK:
        # short delay as readall() returns while the notification is processed
        time.sleep(0.3)

    if mock_gpio.spec.supports_notification:
        for p, cb in enumerate(port_callbacks):
            cb.assert_called_with(p, True)  # noqa: FBT003
    else:
        assert not any(cb.called for cb in port_callbacks)
    mock_gpio.cleanup()
    assert not mock_gpio._poll_thread.is_alive()  # noqa: SLF001
