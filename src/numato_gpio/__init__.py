"""Python API for Numato USB GPIO devices."""

from __future__ import annotations

import threading
import time
from contextlib import suppress
from enum import Enum
from functools import cached_property
from typing import Callable

import serial

from numato_gpio import device_types


class Edge(Enum):
    """Specify the direction of a logic level change.

    Used e.g. for edge detection filtering.
    """

    RISING = 1
    FALLING = 2
    BOTH = 3


class Direction(Enum):
    """Specify the direction of a port."""

    OUT = 0
    IN = 1


ACM_DEVICE_RANGE = range(10)
DEVICE_BUFFER_SIZE = 1000000
DEFAULT_DEVICES = [f"/dev/ttyACM{i}" for i in ACM_DEVICE_RANGE]

devices: dict[int, NumatoUsbGpio] = {}


class NumatoGpioError(RuntimeError):
    """Generic error during GPIO processing."""


class NumatoIoDirError(NumatoGpioError):
    """Wrong port io direction error."""

    def __init__(self, port: int) -> None:
        """Initialize error message."""
        super().__init__(f"Can't write to an input port (port #{port})")


class NumatoAdcPortError(NumatoGpioError):
    """Not an ADC port error."""

    def __init__(self, adc_port: int) -> None:
        """Initialize error message indicating the wrongful ADC port number."""
        super().__init__(
            f"Can't read analog value from port {adc_port} - "
            "that port does not provide an ADC.",
        )


class NumatoUnexpectedResponseError(NumatoGpioError):
    """Wrong ADC value error."""

    def __init__(self, query: str, resp: str, why: str = "") -> None:
        """Initialize error message detailing what and why it's unexpected."""
        super().__init__(
            f"Query '{query!r}' returned unexpected result {resp!r}. {why}",
        )


class NumatoNotifyNotSupportedError(NumatoGpioError):
    """Notify mode is not supported error."""

    def __init__(self, spec: device_types.DeviceSpec, detail: str = "") -> None:
        """Initialize error message mentioning the device name and docs URL."""
        super().__init__(
            f"Notify mode not supported on a {spec.name}. {detail}"
            f"\nSee device docs: {spec.url}",
        )


class NumatoQueryEchoError(NumatoGpioError):
    """Query not echoed correctly by the device."""

    def __init__(self, query: str, echo: str) -> None:
        """Explain the error referring to the query and its unexpected echo."""
        super().__init__(f"Query {query!r} returned unexpected echo {echo!r}")


class NumatoSerialIoError(NumatoGpioError):
    """Wrapper for SerialException errors."""

    def __init__(self, err: serial.SerialException) -> None:
        """Initialize a readable message containing the SerialException message."""
        super().__init__(f"Serial communication failure: {err}")


class NumatoPortOutOfRangeError(NumatoGpioError):
    """Port number out of range for a device."""

    def __init__(self, port: int) -> None:
        """Initialize a readable message containing the out-of-range port number."""
        super().__init__(f"Port number {port} out of range.")


DISCOVER_LOCK = threading.RLock()


def discover(dev_files: list[str] = DEFAULT_DEVICES) -> None:
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
            if not dev.connected:
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
                    raise NumatoGpioError(  # noqa: TRY003, TRY301
                        f"ACM device {device_file} has duplicate device id {device_id}",
                    )

                # success -> add device
                devices[device_id] = gpio
            except (NumatoGpioError, OSError):
                if gpio:
                    gpio.cleanup()
                    del gpio


def cleanup() -> None:
    """Cleanup of all discovered devices' serial connections.

    This is intended to be called during termination of the application or
    during re-configuration before re-discovering the devices.
    """
    for dev_id in list(devices.keys()):
        try:
            devices[dev_id].cleanup()
        except NumatoGpioError:  # noqa: PERF203
            pass  # continue removing other devices
        finally:
            del devices[dev_id]


class NumatoUsbGpio:
    """Low level Numato device interaction.

    Facilitates operations like initialization, reading and manipulating logic
    levels of ports, etc.
    """

    def __init__(self, device: str = "/dev/ttyACM0") -> None:
        """Open a serial connection to a Numato device and initialize it."""
        self.dev_file = device
        self._state = 0
        self._buf = ""
        self._poll_thread = threading.Thread(target=self._poll, daemon=True)
        self._rw_lock = threading.RLock()
        self._can_read = threading.Condition()
        self._ser = serial.Serial(self.dev_file, 19200, timeout=1)
        self._write(b"gpio notify off\r")
        self._drain_ser_buffer()
        self._poll_thread.start()
        self._mask_all_ports = 2**self.spec.ports - 1
        self._hex_digits = self.spec.ports // 4
        self._callback: list[Callable[[int, int], None] | None] = [
            None
        ] * self.spec.ports
        self._edge: list[Edge | None] = [None] * self.spec.ports
        self._ver = None
        try:
            _ = self.id
            _ = self.ver
            self.iodir = self._mask_all_ports  # resets iomask as well
            if self.spec.supports_notification:
                self.notify = False
        except NumatoGpioError as err:
            raise NumatoGpioError(  # noqa: TRY003
                f"Device {self.dev_file} doesn't answer like a numato device: {err}",
            ) from err

    def __del__(self) -> None:
        """Remove the polling-thread."""
        self.cleanup()

    @property
    def connected(self) -> bool:
        """Determine whether a serial connection to the device is established."""
        return self._ser and self._ser.is_open

    @property
    def ver(self) -> str:
        """Return the device's version string."""
        if self._ver is None:
            with self._rw_lock:
                self._ver = self._query_string("ver")
        return self._ver

    @property
    def id(self) -> int:
        """Return the device id as integer value."""
        if not hasattr(self, "_id"):
            with self._rw_lock:
                self._id = self._read_int("id get", 32)
        return self._id

    @id.setter
    def id(self, new_id: int) -> None:
        """Re-program the device id to the value in new_id."""
        self._query_string(f"id set {new_id:08x}")
        self._id = new_id

    @cached_property
    def spec(self) -> device_types.DeviceSpec:
        """Determine and return a specification of the Numato device.

        Devices with 8, 16, 32, 64 and 128 ports are available.
        The determined spec is cached assuming the hardware doesn't change.

        Returns:
            (DeviceSpec): Device specification object

        """
        response = self._query_string("gpio readall")
        hex_digits = len(response)
        ports = hex_digits * 4
        return device_types.spec_from_number_of_ports(ports)

    def setup(self, port: int, *, direction: Direction) -> None:
        """Set up a single port as input or output port."""
        self._check_port_range(port)
        with self._rw_lock:
            new_iodir = (self._iodir & ((1 << port) ^ self._mask_all_ports)) | (
                direction.value << port
            )
            self.iodir = new_iodir

    def cleanup(self) -> None:
        """Reset all ports to input and close the serial connection.

        This is the safe state preventing short circuit of e.g. an enabled
        output port when re-connected to e.g. a grounded input signal.
        """
        with self._rw_lock:
            if self._ser.is_open:
                self.iomask = self._mask_all_ports
                self.iodir = self._mask_all_ports
                if self.spec.supports_notification:
                    self.notify = False
                self._ser.close()
            self._poll_thread.join()

    def write(self, port: int, *, value: int) -> None:
        """Write the logic level of a single port.

        Value can be 1 or True for high, 0 or False for low logic level.
        """
        self._check_port_range(port)
        with self._rw_lock:
            if (self._iodir >> port) & 1:
                raise NumatoIoDirError(port)
            self._state = (self._state & ((1 << port) ^ self._mask_all_ports)) | (
                int(bool(value)) << port
            )
            self.writeall(self._state)

    def read(self, port: int) -> int:
        """Read the logic level of a single port.

        Returns 1 for high or 0 for low level.
        """
        self._check_port_range(port)
        return 1 if self.readall() & (1 << port) else 0

    def adc_read(self, adc_port: int) -> int:
        """Read the voltage level at a given ADC capable port.

        Available ADC ports and their resolutions are listed in the
        device spec object.
        """
        if adc_port not in self.spec.adc_ports:
            raise NumatoAdcPortError(adc_port)
        with self._rw_lock:
            # On devices with more than 32 ports, adc read command **only**
            # accepts two-digit numbers with leading zero.
            #
            # This is vaguely described at the end of "The Command Set"
            # in the documentation:
            # https://numato.com/docs/64-channel-usb-gpio-module-analog-inputs/
            # https://numato.com/docs/128-channel-usb-gpio-module-with-analog-inputs/
            digits = self.spec.adc_port_digits
            query = f"adc read {adc_port:0{digits}}"
            self._query(query)
            try:
                resp = self._read_response()
                return int(resp)
            except ValueError as err:
                raise NumatoUnexpectedResponseError(
                    query,
                    resp,
                    why="Expected a 10 bit decimal integer.",
                ) from err

    @property
    def notify(self) -> bool:
        """Read the notify setting from the device if not already known."""
        if not self.spec.supports_notification:
            # notifications not supported on 8 port devices
            return False

        if not hasattr(self, "_notify"):
            query = "gpio notify get"
            with self._rw_lock:
                self._query(query)
                response = self._read_response()
            if response == "gpio notify enabled":
                self._notify = True
            elif response == "gpio notify disabled":
                self._notify = False
            else:
                raise NumatoUnexpectedResponseError(
                    query,
                    response,
                    why="Expected enabled or disabled.",
                )

        return self._notify

    @notify.setter
    def notify(self, enable: bool) -> None:
        """Enable or disable asynchronous notifications on input port events.

        Callback functions for individual ports can be registered using the
        add_event_detect(...) method. Events are logic level changes on input
        ports.
        """
        if not self.spec.supports_notification:
            # notifications not supported on 8 port devices
            raise NumatoNotifyNotSupportedError(self.spec)

        query = f"gpio notify {'on' if enable else 'off'}"
        expected_response = f"gpio notify {'enabled' if enable else 'disabled'}"

        with self._rw_lock:
            self._query(query)
            self._read_response(expected_response)

        self._notify = enable

    def add_event_detect(
        self,
        port: int,
        callback: Callable[[int, int], None],
        edge: Edge = Edge.BOTH,
    ) -> None:
        """Register a callback for async notifications on input port events.

        An event is triggered by a logic level changes of the particular input
        port. Note that for this mechanism to work you must also enable
        notifications calling notify(True) on this device object.
        """
        if not self.spec.supports_notification:
            raise NumatoNotifyNotSupportedError(
                self.spec,
                detail="Can't install event callback.",
            )
        self._callback[port] = callback
        self._edge[port] = edge

    def remove_event_detect(self, port: int) -> None:
        """Remove a callback function for events on an input port.

        Stops asynchronous calls when that input port's logic level changes.
        """
        self._callback[port] = None
        self._edge[port] = None

    @property
    def iomask(self) -> int:
        """Return the previously set iomask.

        There's no get command for the iomask, so it's set in the constructor
        and its value is cached in a member variable _iomask.
        """
        return self._iomask

    @iomask.setter
    def iomask(self, mask: int) -> None:
        """Write the device's iomask to protect it from unwanted changes.

        Note that the iodir method changes the iomask. Reset the iomask after
        each call to iodir.
        """
        with self._rw_lock:
            self._query(f"gpio iomask {mask:0{self._hex_digits}x}")
            self._read_response("")
            self._iomask = mask

    @property
    def iodir(self) -> int:
        """Get the I/O direction of the device's ports."""
        if not hasattr(self, "_iodir"):
            self._iodir = self._mask_all_ports
        return self._iodir

    @iodir.setter
    def iodir(self, direction: Direction) -> None:
        """Set the input/output port direction configuration for all ports.

        Uses the integer parameter direction as a bit vector with one bit per
        port. Not that this overwrites the iomask to protect the newly defined
        inputs from being written to.
        """
        with self._rw_lock:
            self.iomask = self._mask_all_ports
            self._query(
                f"gpio iodir {direction:0{self._hex_digits}x}",
            )
            self._read_response("")
            self.iomask = direction ^ self._mask_all_ports
            self._iodir = direction

    def readall(self) -> int:
        """Read all ports at once.

        Returns a single int value to be interpreted as bit vector. Note that
        only the input ports may make sense. The output port values may or may
        not reflect the previously written state.
        """
        with self._rw_lock:
            response = self._read_int("gpio readall", self.spec.ports)
            self._state = response
        return self._state

    def writeall(self, bits: int) -> None:
        """Set the logic level of all ports at once.

        Uses the input parameter bits' integer value as 32 bit vector. Only
        output ports are affected.
        """
        with self._rw_lock:
            self._state = bits & ~self._iodir
            self._query(f"gpio writeall {self._state:0{self._hex_digits}x}")
            self._read_response("")

    EOL_BYTES = b"\r\n"

    def _remove_eol(self, sequence: bytes) -> bytes:
        return bytes(x for x in sequence if x not in self.EOL_BYTES)

    def _query(self, query: str) -> None:
        with self._rw_lock:
            self._write(f"{query}\r".encode())
            try:
                self._read_expected_string(query)
            except NumatoGpioError as err:
                raise NumatoQueryEchoError(query, str(err)) from err

    def _write(self, query: bytes) -> None:
        try:
            with self._rw_lock:
                self._ser.write(query)
        except serial.SerialException as err:
            with suppress(OSError):
                self._ser.close()
            raise NumatoSerialIoError(err) from err

    def _read_expected_string(self, expected: str) -> None:
        """Consume an exact string from the input buffer.

        Reads only the amount of characters and ensures that the string matches
        expectations. Otherwise raises an error.

        Doesn't return the string as the user's already got it.
        """
        string = self._read_from_buf(len(expected.encode()))
        # Some devices respond with mixed uppercasing,
        # lowering the response should match expected
        if string.lower() != expected:
            raise NumatoGpioError(string)

    def _query_string(self, query: str) -> str:
        """Send a query and returns the response up to the prompt as a string.

        The answer excludes the end-of-line and prompt characters.
        """
        with self._rw_lock:
            self._query(query)
            return self._read_response()

    def _read_int(self, query: str, bits: int) -> int:
        with self._rw_lock:
            response = self._query_string(query)
            try:
                if len(response) != bits // 4:
                    raise NumatoUnexpectedResponseError(
                        query,
                        response,
                        why=f"Expected response of length {bits // 4}",
                    )
                val = int(response, 16)
            except ValueError as err:
                raise NumatoUnexpectedResponseError(
                    query,
                    response,
                    why=f"Expected a {bits} bit integer in hexadecimal notation.",
                ) from err
        return val

    def _read_response(self, expected: str | None = None) -> str:
        """Read a response up to the terminating prompt.

        Consume the prompt (>) character from the input buffer but do not return it.
        """
        response = ""
        while (read_byte := self._read_from_buf(1)) != ">":
            response += read_byte
        if expected and expected.lower() != response.lower():
            raise NumatoUnexpectedResponseError(
                _query := "",
                response,
                why=f"Expected response {expected!r}",
            )
        return response

    def _read_from_buf(self, num: int) -> str:
        with self._can_read:
            while len(self._buf) < num:
                self._can_read.wait()
            response, self._buf = self._buf[0:num], self._buf[num:]
            return response

    def _serial_read(self, num_bytes: int) -> bytes:
        response = self._ser.read(num_bytes)
        return self._remove_eol(response)

    def _read_notification(self) -> None:
        """Read a notification and call any registered callbacks.

        This method assumes that the leading '#' character has already been read.
        Notification example for a 64 port device configured to all inputs:

            # 0000000000000000 0000000000000001 FFFFFFFFFFFFFFFF
            ^ ^                ^                ^
        start previous value   new value        iodir mask
        """
        self._serial_read(1)
        current_value = int(self._serial_read(self.spec.ports // 4), 16)
        self._serial_read(1)
        previous_value = int(self._serial_read(self.spec.ports // 4), 16)
        self._serial_read(1)
        _ = int(self._serial_read(self.spec.ports // 4), 16)  # read and discard iodir

        edges = current_value ^ previous_value

        def logic_level(port: int) -> bool:
            return bool(current_value & (1 << port))

        def edge_detected(port: int) -> bool:
            return bool(edges & (1 << port))

        def edge_selected(port: int) -> bool:
            lv = logic_level(port)
            return (lv and self._edge[port] in [Edge.RISING, Edge.BOTH]) or (
                not lv and self._edge[port] in [Edge.FALLING, Edge.BOTH]
            )

        for port in range(self.spec.ports):
            if (
                edge_detected(port)
                and edge_selected(port)
                and (cb := self._callback[port]) is not None
            ):
                cb(port, logic_level(port))

    def _poll(self) -> None:
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
                if not (b := self._serial_read(1).decode()):
                    time.sleep(0)
                    continue

                if b != "#":
                    with self._can_read:
                        self._buf += b
                        self._can_read.notify()
                    continue

                self._read_notification()

        except (TypeError, serial.SerialException):
            with suppress(OSError):
                self._ser.close()  # ends the polling loop and its thread

    def _check_port_range(self, port: int) -> None:
        if port not in range(self.spec.ports):
            raise NumatoPortOutOfRangeError(port)

    def _drain_ser_buffer(self) -> None:
        while self._serial_read(DEVICE_BUFFER_SIZE):
            pass

    def __str__(self) -> str:
        """Return human readable string of the device's current state."""
        return " | ".join(
            (
                f"dev: {self.dev_file}",
                f"id: {self.id}",
                f"ver: {self.ver}",
                f"ports: {self.spec.ports}",
                f"iodir: 0x{self.iodir:0{self._hex_digits}x} ",
                f"iomask: 0x{self.iomask:0{self._hex_digits}x}",
                f"state: 0x{self._state:0{self._hex_digits}x}",
            ),
        )
