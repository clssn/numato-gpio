"""Async mockup for pyserial-asyncio connected to a Numato USB GPIO device.

This provides an async version of the serial mock that works with
pyserial-asyncio's StreamReader/StreamWriter interface.
"""  # noqa: INP001

import asyncio
import random
from typing import Any

from numato_gpio.device_types import DeviceType


class AsyncSerialMockNotInitializedError(RuntimeError):
    """Error raised from an AsyncSerialMock object that wasn't properly initialized."""


class AsyncSerialMockBase:
    """Base class for specialized async serial mockup classes."""


class MockStreamReader:
    """Mock asyncio StreamReader for serial communication."""

    def __init__(self, buffer: asyncio.Queue[bytes]) -> None:
        """Initialize mock stream reader."""
        self._buffer = buffer
        self._current_chunk = b""
        self._position = 0

    async def read(self, n: int) -> bytes:
        """Read up to n bytes from the stream."""
        result = b""

        while len(result) < n:
            # If we've consumed the current chunk, get a new one
            if self._position >= len(self._current_chunk):
                # If we have some data already, check if more is available
                if result and self._buffer.empty():
                    # Return what we have so far
                    break

                try:
                    # Wait for data with timeout (shorter if we already have some data)
                    timeout = 0.01 if result else 1.0
                    self._current_chunk = await asyncio.wait_for(
                        self._buffer.get(), timeout=timeout
                    )
                    self._position = 0
                except asyncio.TimeoutError:
                    # Timeout - return what we have
                    break

            # Read from current chunk
            bytes_to_read = min(n - len(result), len(self._current_chunk) - self._position)
            result += self._current_chunk[self._position:self._position + bytes_to_read]
            self._position += bytes_to_read

        return result


class MockStreamWriter:
    """Mock asyncio StreamWriter for serial communication."""

    def __init__(self, device_type: DeviceType, read_buffer: asyncio.Queue[bytes]) -> None:
        """Initialize mock stream writer."""
        self._device_type = device_type
        self._read_buffer = read_buffer
        self._closing = False
        self._closed = False
        self._notify = False
        self._notify_inject_at = 0

    @property
    def eol(self) -> str:
        """Return a random number (0 to 10) of choices of line ending characters.

        Tests that line endings really don't play a role when reading the device
        output.
        """
        eol_chars = "\r\n"
        return "".join(random.choices(eol_chars, k=random.randrange(0, 10)))  # noqa: S311

    def respond(self, query: bytes) -> bytes:
        """Respond to a query, like a Numato device."""
        ports = self._device_type.value.ports
        responses = {
            b"gpio notify off\r": b"gpio notify disabled\n>"
            if self._device_type.value.supports_notification
            else b"",
            b"gpio notify on\r": b"gpio notify enabled\n>"
            if self._device_type.value.supports_notification
            else b"",
            b"gpio notify get\r": b"gpio notify disabled\n>"
            if self._device_type.value.supports_notification
            else b"",
            b"id get\r": b"00004711\n>",
            b"ver\r": b"00000008\n>",
            b"gpio readall\r": f"{'0' * (ports // 4)}\n>".encode(),
            f"gpio writeall {'0' * (ports // 4)}\r".encode(): b">",
            f"gpio iomask {'0' * (ports // 4)}\r".encode(): b">",
            f"gpio iomask {'f' * (ports // 4)}\r".encode(): b">",
            f"gpio iomask {'F' * (ports // 4)}\r".encode(): b">",
            f"gpio iodir {'0' * (ports // 4)}\r".encode(): b">",
            f"gpio iodir {'f' * (ports // 4)}\r".encode(): b">",
            f"gpio iodir {'F' * (ports // 4)}\r".encode(): b">",
        }
        resp = query.replace(b"\r", self.eol.encode())
        resp += responses.get(query, b">").replace(b"\n", self.eol.encode())

        if self._notify:
            msg = "{eol}# {xff} {x00} {xff}".format(
                eol=self.eol,
                xff="F" * (ports // 4),
                x00="0" * (ports // 4),
            )
            resp = (
                resp[: self._notify_inject_at]
                + msg.encode()
                + resp[self._notify_inject_at :]
            )
        return resp

    def write(self, data: bytes) -> None:
        """Write data to the mock device."""
        if self._closing or self._closed:
            raise ConnectionError("Cannot write to closed connection")

        # Process the write and generate response
        response = self.respond(data)

        # Update notify state
        if data == b"gpio notify on\r" and self._device_type.value.supports_notification:
            self._notify = True
        elif data == b"gpio notify off\r" and self._device_type.value.supports_notification:
            self._notify = False

        # Put response in read buffer
        self._read_buffer.put_nowait(response)

    async def drain(self) -> None:
        """Wait for write to complete (no-op for mock)."""
        await asyncio.sleep(0)  # Yield control

    def close(self) -> None:
        """Mark the writer as closing."""
        self._closing = True

    async def wait_closed(self) -> None:
        """Wait for the writer to close."""
        await asyncio.sleep(0)  # Yield control
        self._closed = True

    def is_closing(self) -> bool:
        """Check if the writer is closing."""
        return self._closing


async def async_serialmock(device_type: DeviceType, url: str, **kwargs: Any) -> tuple[MockStreamReader, MockStreamWriter]:
    """Create mock StreamReader and StreamWriter for async serial communication.

    This function mimics serial_asyncio.open_serial_connection.

    Args:
        device_type: The type of Numato device to mock
        url: Device path (ignored in mock)
        **kwargs: Additional arguments (ignored in mock)

    Returns:
        Tuple of (MockStreamReader, MockStreamWriter)
    """
    # Create shared buffer for communication
    read_buffer: asyncio.Queue[bytes] = asyncio.Queue()

    # Create reader and writer
    reader = MockStreamReader(read_buffer)
    writer = MockStreamWriter(device_type, read_buffer)

    return reader, writer


def create_async_serial_mock_factory(device_type: DeviceType):
    """Create a factory function for mocking open_serial_connection.

    Args:
        device_type: The type of Numato device to mock

    Returns:
        Factory function that creates mock reader/writer pair
    """
    async def mock_factory(url: str, **kwargs: Any) -> tuple[MockStreamReader, MockStreamWriter]:
        return await async_serialmock(device_type, url, **kwargs)

    return mock_factory
