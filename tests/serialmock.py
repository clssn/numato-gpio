import threading


def gen_serial(eol):
    class SerialMock:
        """Mockup for a Numato USB IO expander device behind a serial device."""

        ports = None

        def respond(self, input):
            responses = {
                b"gpio notify off\r": b"gpio notify disabled\n>"
                if self.ports != 8
                else b"",
                b"gpio notify on\r": b"gpio notify enabled\n>"
                if self.ports != 8
                else b"",
                b"id get\r": b"00004711\n>",
                b"ver\r": b"00000008\n>",
                b"gpio readall\r": f'{"0"*(self.ports//4)}\n>'.encode(),
                f'gpio writeall {"0"*(self.ports//4)}\r'.encode(): b">",
                f'gpio iomask {"0"*(self.ports//4)}\r'.encode(): b">",
                f'gpio iomask {"f"*(self.ports//4)}\r'.encode(): b">",
                f'gpio iomask {"F"*(self.ports//4)}\r'.encode(): b">",
                f'gpio iodir {"0"*(self.ports//4)}\r'.encode(): b">",
                f'gpio iodir {"f"*(self.ports//4)}\r'.encode(): b">",
                f'gpio iodir {"F"*(self.ports//4)}\r'.encode(): b">",
            }
            resp = input.decode().replace("\r", self.eol)
            resp += responses[input].decode().replace("\n", self.eol)
            if self.notify:
                msg = "{eol}# {xff} {x00} {xff}".format(
                    eol=self.eol,
                    xff="F" * (self.ports // 4),
                    x00="0" * (self.ports // 4),
                )
                resp = (
                    resp[: self.notify_inject_at] + msg + resp[self.notify_inject_at :]
                )
            return resp.encode()

        def __init__(self, file, speed, timeout):
            self.file = file
            self.speed = speed
            self.timeout = timeout
            self.buf = b""
            self.lock = threading.RLock()
            self.is_open = True
            self.eol = eol
            self.notify = False
            self.notify_inject_at = 0

        def write(self, input):
            """Write to the mocked device.

            Processes the written data and generates the output in the buffer."""
            with self.lock:

                self.buf += self.respond(input)

                if input == b"gpio notify on\r" and self.ports != 8:
                    self.notify = True
                if input == b"gpio notify off\r" and self.ports != 8:
                    self.notify = False

        def read(self, size):
            """Read size bytes from the mocked device buffer."""
            with self.lock:
                size = min(size, len(self.buf))
                buf, self.buf = self.buf[:size], self.buf[size:]
            return buf

        def close(self):
            """Close the mocked device."""
            self.is_open = False

    return SerialMock
