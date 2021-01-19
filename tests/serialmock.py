import threading

def gen_serial(eol):
    class SerialMock:
        """Mockup for a pyserial Serial object connected to a Numato USB IO expander device."""
        def respond(self, input):
            responses = {
                b'gpio notify off\r': b'gpio notify disabled\n>',
                b'id get\r': b'00004711\n>',
                b'ver\r': b'00000008\n>',
                b'gpio iomask ffffffff\r': b'>',
                b'gpio iomask 00000000\r': b'>',
                b'gpio iodir ffffffff\r': b'>',
            }
            return responses[input].decode().replace("\n", self.eol).encode()

        def __init__(self, file, speed, timeout):
            self.file = file
            self.speed = speed
            self.timeout = timeout
            self.buf = b''
            self.lock = threading.RLock()
            self.is_open = True
            self.eol = eol

        def write(self, input):
            """Write to the mocked device.

            Processes the written data and generates the output in the buffer."""
            with self.lock:
                self.buf = input.decode().replace("\r", self.eol).encode() + self.respond(input)

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
