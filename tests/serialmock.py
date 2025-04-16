"""Mockup for a pyserial object connected to a Numato USB GPIO device.

Responds much like a device, with quite a few abstractions".
"""  # noqa: INP001

import random
import threading


class SerialMockNotInitializedError(RuntimeError):
    """Error raised from a SerialMock object that wasn't properly initialized."""


class SerialMock:
    """Mockup for a Numato USB IO expander device behind a serial device."""

    ports = None

    @property
    def _can_notify(self) -> bool:
        return self.ports != (_num_device_ports_where_notify_unsupported := 8)

    def respond(self, query: str) -> bytes:
        """Respond to a query, like a Numato device."""
        if self.ports is None:
            msg = "SerialMock ports is None"
            raise SerialMockNotInitializedError(msg)

        responses = {
            b"gpio notify off\r": b"gpio notify disabled\n>"
            if self._can_notify
            else b"",
            b"gpio notify on\r": b"gpio notify enabled\n>" if self._can_notify else b"",
            b"id get\r": b"00004711\n>",
            b"ver\r": b"00000008\n>",
            b"gpio readall\r": f"{'0' * (self.ports // 4)}\n>".encode(),
            f"gpio writeall {'0' * (self.ports // 4)}\r".encode(): b">",
            f"gpio iomask {'0' * (self.ports // 4)}\r".encode(): b">",
            f"gpio iomask {'f' * (self.ports // 4)}\r".encode(): b">",
            f"gpio iomask {'F' * (self.ports // 4)}\r".encode(): b">",
            f"gpio iodir {'0' * (self.ports // 4)}\r".encode(): b">",
            f"gpio iodir {'f' * (self.ports // 4)}\r".encode(): b">",
            f"gpio iodir {'F' * (self.ports // 4)}\r".encode(): b">",
        }
        resp = query.decode().replace("\r", self.eol)
        resp += responses[query].decode().replace("\n", self.eol)
        if self.notify:
            msg = "{eol}# {xff} {x00} {xff}".format(
                eol=self.eol,
                xff="F" * (self.ports // 4),
                x00="0" * (self.ports // 4),
            )
            resp = resp[: self.notify_inject_at] + msg + resp[self.notify_inject_at :]
        return resp.encode()

    def __init__(self, file: str, speed: int, timeout: int) -> None:
        """Initialize the pseudo serial object."""
        self.file = file
        self.speed = speed
        self.timeout = timeout
        self.buf = b""
        self.lock = threading.RLock()
        self.is_open = True
        self.notify = False
        self.notify_inject_at = 0

    @property
    def eol(self) -> str:
        """Return a random number (0 to 10) of choices of line ending characters.

        Tests that line endings really don't play a role when reading the device output.
        """
        eol_chars = "\r\n"
        return "".join(random.choices(eol_chars, k=random.randrange(0, 10)))  # noqa: S311

    def write(self, query: str) -> None:
        """Write to the mocked device.

        Processes the written data and generates the output in the buffer.
        """
        with self.lock:
            self.buf += self.respond(query)

            if query == b"gpio notify on\r" and self._can_notify:
                self.notify = True
            if query == b"gpio notify off\r" and self._can_notify:
                self.notify = False

    def read(self, size: int) -> bytes:
        """Read size bytes from the mocked device buffer."""
        with self.lock:
            size = min(size, len(self.buf))
            buf, self.buf = self.buf[:size], self.buf[size:]
        return buf

    def close(self) -> None:
        """Close the mocked device."""
        self.is_open = False
