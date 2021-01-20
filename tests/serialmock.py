import math
import threading

def gen_serial(eol):
    class SerialMock:
        """Mockup for a pyserial Serial object connected to a Numato USB IO expander device."""
        ports = None
        def respond(self, input):
            responses = {
                b'gpio notify off\r': b'gpio notify disabled\n>' if self.ports != 8 else b'',
                b'id get\r': b'00004711\n>',
                b'ver\r': b'00000008\n>',
                b'gpio readall\r': f'{"0"*(self.ports//4)}\n>'.encode(),
                f'gpio iomask {"0"*(self.ports//4)}\r'.encode(): b'>',
                f'gpio iomask {"f"*(self.ports//4)}\r'.encode(): b'>',
                f'gpio iomask {"F"*(self.ports//4)}\r'.encode(): b'>',
                f'gpio iodir {"0"*(self.ports//4)}\r'.encode(): b'>',
                f'gpio iodir {"f"*(self.ports//4)}\r'.encode(): b'>',
                f'gpio iodir {"F"*(self.ports//4)}\r'.encode(): b'>',
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
