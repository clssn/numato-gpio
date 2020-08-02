"""Python API for 32 Port Numato USB GPIO devices."""

import serial
import threading

# Edge detection
RISING = 1
FALLING = 2
BOTH = 3

# Port direction
OUT = 0
IN = 1

ACM_DEVICE_RANGE = range(10)
DEVICE_BUFFER_SIZE = 1000000
DEFAULT_DEVICES = ["/dev/ttyACM{}".format(i) for i in ACM_DEVICE_RANGE]

devices = dict()


class NumatoGpioError(Exception):
    pass


DISCOVER_LOCK = threading.RLock()


def discover(dev_files=DEFAULT_DEVICES):
    """Scan a set of unix device files to find Numato USB devices.

    Devices are made available via the "devices" dict with the device id read
    from the device (NOT the postfix index of the unix device file). E.g.
    devices(2) is in general NOT the /dev/ttyACM2 device, but is the device
    that returned 2 when queried with "id get".

    You may wish to set individual ids for your devices and label them
    accordingly to prevent mistakes during configuration which may damage the
    device. You can use the gnu screen terminal emulation program like this to
    assign e.g. id 5:

    1) Plug in (only) the device to assign an id to so it'll get /dev/ttyACM0
    2) Wait a couple of seconds as your Linux OS may be trying to identify the
       device as a Modem right after plugging it in.
    3) # screen /dev/ttyACM0
    4) id set 00000005
    5) Quit screen with: Ctrl-a + \
    """
    with DISCOVER_LOCK:
        # remove disconnected
        for dev_id, dev in list(devices.items()):
            if not (dev._ser and dev._ser.is_open):
                del devices[dev_id]

        # discover newly connected
        for device_file in dev_files:
            gpio = None
            # device already registered?
            if device_file in (dev.dev_file for dev in devices.values()):
                continue
            try:
                gpio = NumatoUsbGpio(device_file)

                # device id unique?
                device_id = gpio.id
                if device_id in devices:
                    raise NumatoGpioError(
                        "ACM device {} has duplicate device id {}".format(
                            device_file, device_id))

                # success -> add device
                devices[device_id] = gpio
            except (NumatoGpioError, OSError):
                if gpio:
                    gpio.cleanup()
                    del gpio


def cleanup():
    """Cleanup of all discovered devices' serial connections.

    This is inteded to be called during termination of the application or
    during re-configuration before re-discovering the devices.
    """
    for dev_id in list(devices.keys()):
        try:
            devices[dev_id].cleanup()
        except NumatoGpioError:
            pass  # continue removing other devices
        finally:
            del devices[dev_id]


class NumatoUsbGpio:
    """Low level Numato device interaction.

    Facilitates operations like initialization, reading and manipulating logic
    levels of ports, etc.
    """
    def __init__(self, device="/dev/ttyACM0"):
        """Open a serial connection to a Numato device and initialize it."""

        self.dev_file = device
        self._state = 0
        self._buf = ""
        self._poll_thread = threading.Thread(target=self._poll)
        self._rw_lock = threading.RLock()
        self._can_read = threading.Condition()
        self._callback = [0] * 32
        self._edge = [None] * 32
        self._ser = serial.Serial(self.dev_file, 19200, timeout=1)
        self._write("gpio notify off\r".encode())
        self._drain_ser_buffer()
        self._poll_thread.start()
        try:
            _ = self.id
            _ = self.ver
            self.iodir = 0xFFFFFFFF  # resets iomask as well
            self.notify = False
        except NumatoGpioError as err:
            raise NumatoGpioError(
                "Device {} doesn't answer like a numato device: {}".format(
                    self.dev_file, err))

    @property
    def ver(self):
        """Return the device's version number as an integer value."""
        if not hasattr(self, "_ver"):
            with self._rw_lock:
                self._ver = self._read_int32("ver")
        return self._ver

    @property
    def id(self):
        """Return the device id as integer value."""
        if not hasattr(self, "_id"):
            with self._rw_lock:
                self._id = self._read_int32("id get")
        return self._id

    @id.setter
    def id(self, new_id):
        """Re-program the device id to the value in new_id."""
        self._query("id set {:08x}".format(new_id), expected=">")
        self._id = new_id

    def setup(self, port, direction):
        """Set up a single port as input or output port."""
        self._check_port_range(port)
        with self._rw_lock:
            new_iodir = (self._iodir & ((1 << port) ^ 0xFFFFFFFF)) | (
                (0 if not direction else 1) << port)
            self.iodir = new_iodir

    def cleanup(self):
        """Reset all ports to input and close the serial connection.

        This is the safe state preventing short circuit of e.g. an enabled
        output port when re-connected to e.g. a grounded input signal.
        """
        with self._rw_lock:
            self.iomask = 0xFFFFFFFF
            self.iodir = 0xFFFFFFFF
            self.notify = False
            self._ser.close()

    def write(self, port, value):
        """Write the logic level of a single port.

        Value can be 1 or True for high, 0 or False for low logic level.
        """
        self._check_port_range(port)
        with self._rw_lock:
            if (self._iodir >> port) & 1:
                raise NumatoGpioError("Can't write to input port")
            self._state = (self._state & ((1 << port) ^ 0xFFFFFFFF)) | (
                (0 if not value else 1) << port)
            self.writeall(self._state)

    def read(self, port):
        """Read the logic level of a single port.

        Returns 1 for high or 0 for low level.
        """
        self._check_port_range(port)
        return 1 if self.readall() & (1 << port) else 0

    def adc_read(self, adc_port):
        """Read the voltage level at a given ADC capable port.

        Ports 1 to 7 are ADC capable if configured as input. ADC values range
        from 0 (0V) to 1023 (3.3V). Note that ADCs have a certain tolerance.
        """
        if adc_port not in range(1, 8):
            raise NumatoGpioError(
                "Can't read analog value from port {} - "
                "only ports 1 to 7 are ADC capable.".format(adc_port))
        with self._rw_lock:
            query = "adc read {}\r".format(adc_port)
            self._query(query)
            resp = self._read_until(">")
            try:
                return int(resp[:resp.find("\r")])
            except ValueError:
                raise NumatoGpioError(
                    "Query '{}' returned unexpected result {}. "
                    "Expected 10 bit decimal integer.".format(query, resp))

    @property
    def notify(self):
        """Read the notify setting from the device if not already known."""
        if not hasattr(self, "_notify"):
            query = "gpio notify get\r"
            expected = "gpio notify "
            with self._rw_lock:
                self._query(query, expected=expected)
                response = self._read_until(">")
            if response.startswith("enabled"):
                self._notify = True
            elif response.startswith("disabled"):
                self._notify = False
            else:
                raise NumatoGpioError(
                    "Expected enabled or disabled, but got: {}".format(
                        response.encode()))

    @notify.setter
    def notify(self, enable):
        """Enable or disable asynchronous notifications on input port events.

        Callback functions for individual ports can be registered using the
        add_event_detect(...) method. Events are logic level changes on input
        ports.
        """
        query = "gpio notify {}".format("on" if enable else "off")
        expected_response = "gpio notify {}\r\n>".format(
            "enabled" if enable else "disabled")
        with self._rw_lock:
            self._query(query, expected=expected_response)
        self._notify = enable

    def add_event_detect(self, port, callback, edge=BOTH):
        """Register a callback for async notifications on input port events.

        An event is triggered by a logic level changes of the particular input
        port. Note that for this mechanism to work you must also enable
        notifications calling notify(True) on this device object.
        """
        self._callback[port] = callback
        self._edge[port] = edge

    def remove_event_detect(self, port):
        """Remove a callback function for events on an input port.

        Stops asynchronous calls when that input port's logic level changes.
        """
        self._callback[port] = None
        self._edge[port] = None

    @property
    def iomask(self):
        """Return the previously set iomask.

        There's no get command for the iomask, so it's set in the constructor
        and its value is cached in a member variable _iomask."""
        return self._iomask

    @iomask.setter
    def iomask(self, mask):
        """Write the device's iomask to protect it from unwanted changes.

        Note that the iodir method changes the iomask. Reset the iomask after
        each call to iodir.
        """
        with self._rw_lock:
            self._query("gpio iomask {:08x}".format(mask), expected=">")
            self._iomask = mask

    @property
    def iodir(self):
        if not hasattr(self, "_iodir"):
            self._iodir = 0xFFFFFFFF
        return self._iodir

    @iodir.setter
    def iodir(self, direction):
        """Set the input/output port direction configuration for all ports.

        Uses the integer parameter direction as a single 32 bit vector.
        Not that this overwrites the iomask to protect the newly defined inputs
        from being written to.
        """
        with self._rw_lock:
            self.iomask = 0xFFFFFFFF
            self._query("gpio iodir {:08x}".format(direction), expected=">")
            self.iomask = direction ^ 0xFFFFFFFF
            self._iodir = direction

    def readall(self):
        """Read all 32 bits at once.

        Returns a single int value to be interpreted as bit vector. Note that
        only the input ports may make sense. The output port values may or may
        not reflect the previously written state.
        """
        with self._rw_lock:
            response = self._read_int32("gpio readall")
            self._state = response
        return self._state

    def writeall(self, bits):
        """Set the logic level of all ports at once.

        Uses the input parameter bits' integer value as 32 bit vector. Only
        output ports are affected.
        """
        with self._rw_lock:
            self._state = bits & ~self._iodir
            self._query("gpio writeall {:08x}".format(self._state),
                        expected=">")

    def _query(self, query, expected=None):
        with self._rw_lock:
            self._write("{}\r".format(query).encode())
            expected_echo = "{}\r\n".format(query)
            try:
                self._read_string(expected_echo)
            except NumatoGpioError as err:
                raise NumatoGpioError(
                    "Query '{}' returned unexpected echo {}".format(
                        query, str(err)))
            if not expected:
                return
            try:
                self._read_string(expected)
            except NumatoGpioError as err:
                raise NumatoGpioError(
                    "Query '{}' returned unexpected response {}".format(
                        query, str(err)))

    def _write(self, query):
        try:
            with self._rw_lock:
                self._ser.write(query)
        except serial.serialutil.SerialException:
            self._ser.close()
            raise NumatoGpioError("Serial communication failure")

    def _read_string(self, expected):
        string = self._read(len(expected.encode()))
        if string != expected:
            raise NumatoGpioError(string)

    def _read_int32(self, query):
        with self._rw_lock:
            self._query(query)
            response = self._read(8)
            try:
                val = int(response, 16)
                self._read_string("\r\n>")
            except ValueError:
                raise NumatoGpioError(
                    "Query '{}' returned unexpected result {}. "
                    "Expected 32 bit hexadecimal integer.".format(
                        query, response))
            except NumatoGpioError as err:
                raise NumatoGpioError(
                    "Unexpected string {} after successful query {}".format(
                        str(err), query))
        return val

    def _read_until(self, end_str):
        response = ""
        while not response.endswith(end_str):
            response += self._read(1)
        return response

    def _read(self, num):
        self._can_read.acquire()
        while len(self._buf) < num:
            self._can_read.wait()
        response, self._buf = self._buf[0:num], self._buf[num:]
        self._can_read.release()
        return response

    def _poll(self):
        """Read data and process and notifications from the Numato device.

        Reads characters from the serial device and detects edge notifications
        which can interrupt the normal data at any point. Callbacks registered
        for the particular port and type of edge are processed immediately.

        This method shall be started as an extra thread. It returns only when
        the serial connection is closed or an exception is caught while
        reading.
        """
        try:
            while self._ser and self._ser.is_open:

                def read_notification():
                    buf = self._ser.read(1).decode()
                    if not buf:
                        return None, None, buf
                    if buf != "\r":
                        return None, None, buf
                    # could be a notification
                    buf += self._ser.read(1).decode()
                    if not buf.endswith("\r\n"):
                        return None, None, buf
                    # could still be a notification
                    buf += self._ser.read(1).decode()
                    if not buf.endswith("\r\n#"):
                        return None, None, buf
                    # notification detected!
                    self._ser.read(1)
                    current_value = int(self._ser.read(8), 16)
                    self._ser.read(1)
                    previous_value = int(self._ser.read(8), 16)
                    self._ser.read(1)
                    self._ser.read(8)  # read and discard iodir
                    return current_value, previous_value, None

                current_value, previous_value, buf = read_notification()
                if current_value and previous_value:
                    edges = current_value ^ previous_value

                    def logic_level(port):
                        return bool(current_value & (1 << port))

                    def edge_detected(port):
                        return bool(edges & (1 << port))

                    def edge_selected(port):
                        lv = logic_level(port)
                        return (lv and self._edge[port] in [RISING, BOTH]) or (
                            not lv and self._edge[port] in [FALLING, BOTH])

                    for port in range(32):
                        if edge_detected(port) and edge_selected(port):
                            self._callback[port](port, logic_level(port))
                elif buf:
                    self._can_read.acquire()
                    self._buf += buf
                    self._can_read.notify()
                    self._can_read.release()
        except (TypeError, serial.serialutil.SerialException):
            self._ser.close()
            pass  # ends the polling loop and its thread

    def _check_port_range(self, port):
        if port not in range(32):
            raise NumatoGpioError("Port number {} out of range.".format(port))

    def _drain_ser_buffer(self):
        while self._ser.read(DEVICE_BUFFER_SIZE):
            pass

    def __str__(self):
        """Return human readable string of the device's curent state."""
        return ("dev: {} | id: {} | ver: {} | iodir: 0x{:08x} | "
                "iomask: 0x{:08x} | state: 0x{:08x}".format(
                    self.dev_file, self.id, self.ver, self.iodir, self.iomask,
                    self._state))
