"""Async Python API for Numato USB GPIO devices.

This module provides an asynchronous alternative to the synchronous/multithreaded
API in the main numato_gpio module. It uses asyncio and pyserial-asyncio for
non-blocking I/O operations.

Example usage:
    import asyncio
    from numato_gpio.async_api import NumatoUsbGpioAsync, discover_async

    async def main():
        # Discover devices
        await discover_async()

        # Get a device
        device = devices_async[0]

        # Setup and use a port
        await device.setup(0, direction=Direction.OUT)
        await device.write(0, value=1)
        value = await device.read(0)

        # Cleanup
        await device.cleanup()

    asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import inspect
import time
from contextlib import suppress
from functools import cached_property
from typing import Awaitable, Callable

import serial
import serial_asyncio  # type: ignore[import-untyped]

from numato_gpio import device_types
from numato_gpio import (
    Direction,
    Edge,
    NumatoAdcPortError,
    NumatoCleanupError,
    NumatoGpioError,
    NumatoIoDirError,
    NumatoNotifyNotSupportedError,
    NumatoPortOutOfRangeError,
    NumatoQueryEchoError,
    NumatoSerialIoError,
    NumatoUnexpectedResponseError,
)

ACM_DEVICE_RANGE = range(10)
DEVICE_BUFFER_SIZE = 1000000
DEFAULT_DEVICES = [f"/dev/ttyACM{i}" for i in ACM_DEVICE_RANGE]

devices_async: dict[int, NumatoUsbGpioAsync] = {}

# Lock for device discovery
_discover_lock = asyncio.Lock()


async def discover_async(dev_files: list[str] = DEFAULT_DEVICES) -> None:
    """Scan a set of unix device files to find Numato USB devices (async version).

    Devices are made available via the "devices_async" dict with the device id read
    from the device (NOT the postfix index of the unix device file). E.g.
    devices_async[2] is in general NOT the /dev/ttyACM2 device, but is the device
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
    5) Quit screen with: Ctrl-a + \\
    """
    async with _discover_lock:
        # remove disconnected
        for dev_id, dev in list(devices_async.items()):
            if not dev.connected:
                del devices_async[dev_id]

        # discover newly connected
        for device_file in dev_files:
            gpio = None
            # device already registered?
            if device_file in (dev.dev_file for dev in devices_async.values()):
                continue
            try:
                gpio = await NumatoUsbGpioAsync.create(device_file)

                # device id unique?
                device_id = await gpio.get_id()
                if device_id in devices_async:
                    raise NumatoGpioError(  # noqa: TRY003, TRY301
                        f"ACM device {device_file} has duplicate device id {device_id}",
                    )

                # success -> add device
                devices_async[device_id] = gpio
            except (NumatoGpioError, OSError):
                if gpio:
                    await gpio.cleanup()
                    del gpio


async def cleanup_async() -> None:
    """Cleanup of all discovered devices' serial connections (async version).

    This is intended to be called during termination of the application or
    during re-configuration before re-discovering the devices.
    """
    for dev_id in list(devices_async.keys()):
        try:
            await devices_async[dev_id].cleanup()
        except NumatoGpioError:  # noqa: PERF203
            pass  # continue removing other devices
        finally:
            del devices_async[dev_id]


class NumatoUsbGpioAsync:
    """Async low level Numato device interaction.

    Facilitates operations like initialization, reading and manipulating logic
    levels of ports, etc. This is the async version using asyncio for non-blocking
    I/O operations.

    Note: Use the create() class method instead of __init__ for proper async initialization.
    """

    def __init__(self, device: str = "/dev/ttyACM0") -> None:
        """Initialize the device object (sync part only).

        Do not call this directly. Use the create() class method instead.
        """
        self.dev_file = device
        self._state = 0
        self._buf = ""
        self._rw_lock = asyncio.Lock()
        self._buf_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._poll_task: asyncio.Task[None] | None = None
        self._mask_all_ports = 0
        self._hex_digits = 0
        self._callback: list[Callable[[int, int], None | Awaitable[None]] | None] = []
        self._edge: list[Edge | None] = []
        self._ver: str | None = None
        self._id: int | None = None
        self._iodir: int = 0
        self._iomask: int = 0
        self._notify: bool = False
        self._spec: device_types.DeviceSpec | None = None

    @classmethod
    async def create(cls, device: str = "/dev/ttyACM0") -> NumatoUsbGpioAsync:
        """Create and initialize a Numato device connection (async factory method).

        Args:
            device: Device file path (e.g., "/dev/ttyACM0")

        Returns:
            Initialized NumatoUsbGpioAsync instance

        Raises:
            NumatoGpioError: If device doesn't respond like a Numato device
        """
        self = cls(device)
        await self._initialize()
        return self

    async def _initialize(self) -> None:
        """Initialize the device connection and settings."""
        try:
            # Open serial connection
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self.dev_file,
                baudrate=19200,
            )

            # Disable notifications initially
            async with self._rw_lock:
                await self._write(b"gpio notify off\r")
            await self._drain_ser_buffer()

            # Start polling task
            self._poll_task = asyncio.create_task(self._poll())

            # Get device spec and initialize
            spec = await self.get_spec()
            self._mask_all_ports = 2**spec.ports - 1
            self._hex_digits = spec.ports // 4
            self._callback = [None] * spec.ports
            self._edge = [None] * spec.ports

            # Initialize device properties
            _ = await self.get_id()
            _ = await self.get_ver()
            await self.set_iodir(self._mask_all_ports)  # resets iomask as well
            if spec.supports_notification:
                await self.set_notify(False)

        except NumatoGpioError as err:
            raise NumatoGpioError(  # noqa: TRY003
                f"Device {self.dev_file} doesn't answer like a numato device: {err}",
            ) from err

    @property
    def connected(self) -> bool:
        """Determine whether a serial connection to the device is established."""
        return self._writer is not None and not self._writer.is_closing()

    async def get_ver(self) -> str:
        """Return the device's version string."""
        if self._ver is None:
            async with self._rw_lock:
                self._ver = await self._query_string("ver")
        return self._ver

    async def get_id(self) -> int:
        """Return the device id as integer value."""
        if self._id is None:
            async with self._rw_lock:
                self._id = await self._read_int("id get", 32)
        return self._id

    async def set_id(self, new_id: int) -> None:
        """Re-program the device id to the value in new_id."""
        await self._query_string(f"id set {new_id:08x}")
        self._id = new_id

    async def get_spec(self) -> device_types.DeviceSpec:
        """Determine and return a specification of the Numato device.

        Devices with 8, 16, 32, 64 and 128 ports are available.
        The determined spec is cached assuming the hardware doesn't change.

        Returns:
            DeviceSpec: Device specification object
        """
        if self._spec is None:
            response = await self._query_string("gpio readall")
            hex_digits = len(response)
            ports = hex_digits * 4
            self._spec = device_types.spec_from_number_of_ports(ports)
        return self._spec

    async def setup(self, port: int, *, direction: Direction) -> None:
        """Set up a single port as input or output port."""
        spec = await self.get_spec()
        self._check_port_range(port, spec)
        async with self._rw_lock:
            new_iodir = (self._iodir & ((1 << port) ^ self._mask_all_ports)) | (
                direction.value << port
            )
            await self.set_iodir(new_iodir)

    async def cleanup(self) -> None:
        """Reset all ports to input and close the serial connection.

        This is the safe state preventing short circuit of e.g. an enabled
        output port when re-connected to e.g. a grounded input signal.
        """
        async with self._rw_lock:
            if self._writer and not self._writer.is_closing():
                spec = await self.get_spec()
                with suppress(NumatoGpioError):
                    await self.set_iomask(self._mask_all_ports)
                    await self.set_iodir(self._mask_all_ports)
                    if spec.supports_notification:
                        await self.set_notify(False)
                self._writer.close()
                await self._writer.wait_closed()

            if self._poll_task and not self._poll_task.done():
                self._poll_task.cancel()
                try:
                    await asyncio.wait_for(self._poll_task, timeout=1.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                if not self._poll_task.done():
                    raise NumatoCleanupError(self)

    async def write(self, port: int, *, value: int) -> None:
        """Write the logic level of a single port.

        Value can be 1 or True for high, 0 or False for low logic level.
        """
        spec = await self.get_spec()
        self._check_port_range(port, spec)
        async with self._rw_lock:
            if (self._iodir >> port) & 1:
                raise NumatoIoDirError(port)
            self._state = (self._state & ((1 << port) ^ self._mask_all_ports)) | (
                int(bool(value)) << port
            )
            await self.writeall(self._state)

    async def read(self, port: int) -> int:
        """Read the logic level of a single port.

        Returns 1 for high or 0 for low level.
        """
        spec = await self.get_spec()
        self._check_port_range(port, spec)
        all_values = await self.readall()
        return 1 if all_values & (1 << port) else 0

    async def adc_read(self, adc_port: int) -> int:
        """Read the voltage level at a given ADC capable port.

        Available ADC ports and their resolutions are listed in the
        device spec object.
        """
        spec = await self.get_spec()
        if adc_port not in spec.adc_ports:
            raise NumatoAdcPortError(adc_port)
        async with self._rw_lock:
            # On devices with more than 32 ports, adc read command **only**
            # accepts two-digit numbers with leading zero.
            #
            # This is vaguely described at the end of "The Command Set"
            # in the documentation:
            # https://numato.com/docs/64-channel-usb-gpio-module-analog-inputs/
            # https://numato.com/docs/128-channel-usb-gpio-module-with-analog-inputs/
            digits = spec.adc_port_digits
            query = f"adc read {adc_port:0{digits}}"
            await self._query(query)
            try:
                resp = await self._read_response()
                return int(resp)
            except ValueError as err:
                raise NumatoUnexpectedResponseError(
                    query,
                    resp,
                    why="Expected a 10 bit decimal integer.",
                ) from err

    async def get_notify(self) -> bool:
        """Read the notify setting from the device if not already known."""
        spec = await self.get_spec()
        if not spec.supports_notification:
            # notifications not supported on 8 port devices
            return False

        if not self._notify:
            query = "gpio notify get"
            async with self._rw_lock:
                await self._query(query)
                response = await self._read_response()
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

    async def set_notify(self, enable: bool) -> None:
        """Enable or disable asynchronous notifications on input port events.

        Callback functions for individual ports can be registered using the
        add_event_detect(...) method. Events are logic level changes on input
        ports.
        """
        spec = await self.get_spec()
        if not spec.supports_notification:
            # notifications not supported on 8 port devices
            raise NumatoNotifyNotSupportedError(spec)

        query = f"gpio notify {'on' if enable else 'off'}"
        expected_response = f"gpio notify {'enabled' if enable else 'disabled'}"

        async with self._rw_lock:
            await self._query(query)
            await self._read_response(expected_response)

        self._notify = enable

    async def add_event_detect(
        self,
        port: int,
        callback: Callable[[int, int], None | Awaitable[None]],
        edge: Edge = Edge.BOTH,
    ) -> None:
        """Register a callback for async notifications on input port events.

        An event is triggered by a logic level changes of the particular input
        port. Note that for this mechanism to work you must also enable
        notifications calling set_notify(True) on this device object.

        The callback can be either a regular function or an async coroutine.
        """
        spec = await self.get_spec()
        if not spec.supports_notification:
            raise NumatoNotifyNotSupportedError(
                spec,
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

    async def get_iomask(self) -> int:
        """Return the previously set iomask.

        There's no get command for the iomask, so it's set in the constructor
        and its value is cached in a member variable _iomask.
        """
        return self._iomask

    async def set_iomask(self, mask: int) -> None:
        """Write the device's iomask to protect it from unwanted changes.

        Note that the set_iodir method changes the iomask. Reset the iomask after
        each call to set_iodir.
        """
        async with self._rw_lock:
            await self._query(f"gpio iomask {mask:0{self._hex_digits}x}")
            await self._read_response("")
            self._iomask = mask

    async def get_iodir(self) -> int:
        """Get the I/O direction of the device's ports."""
        return self._iodir

    async def set_iodir(self, direction: int) -> None:
        """Set the input/output port direction configuration for all ports.

        Uses the integer parameter direction as a bit vector with one bit per
        port. Note that this overwrites the iomask to protect the newly defined
        inputs from being written to.
        """
        async with self._rw_lock:
            await self.set_iomask(self._mask_all_ports)
            await self._query(
                f"gpio iodir {direction:0{self._hex_digits}x}",
            )
            await self._read_response("")
            await self.set_iomask(direction ^ self._mask_all_ports)
            self._iodir = direction

    async def readall(self) -> int:
        """Read all ports at once.

        Returns a single int value to be interpreted as bit vector. Note that
        only the input ports may make sense. The output port values may or may
        not reflect the previously written state.
        """
        spec = await self.get_spec()
        async with self._rw_lock:
            response = await self._read_int("gpio readall", spec.ports)
            self._state = response
        return self._state

    async def writeall(self, bits: int) -> None:
        """Set the logic level of all ports at once.

        Uses the input parameter bits' integer value as bit vector. Only
        output ports are affected.
        """
        async with self._rw_lock:
            self._state = bits & ~self._iodir
            await self._query(f"gpio writeall {self._state:0{self._hex_digits}x}")
            await self._read_response("")

    EOL_BYTES = b"\r\n"

    def _remove_eol(self, sequence: bytes) -> bytes:
        return bytes(x for x in sequence if x not in self.EOL_BYTES)

    async def _query(self, query: str) -> None:
        async with self._rw_lock:
            await self._write(f"{query}\r".encode())
            try:
                await self._read_expected_string(query)
            except NumatoGpioError as err:
                raise NumatoQueryEchoError(query, str(err)) from err

    async def _write(self, query: bytes) -> None:
        """Write to serial connection. Caller must hold _rw_lock."""
        try:
            if self._writer:
                self._writer.write(query)
                await self._writer.drain()
        except (serial.SerialException, OSError) as err:
            if self._writer:
                with suppress(OSError):
                    self._writer.close()
                    await self._writer.wait_closed()
            raise NumatoSerialIoError(err) from err

    async def _read_expected_string(self, expected: str) -> None:
        """Consume an exact string from the input buffer.

        Reads only the amount of characters and ensures that the string matches
        expectations. Otherwise raises an error.

        Doesn't return the string as the user's already got it.
        """
        string = await self._read_from_buf(len(expected.encode()))
        # Some devices respond with mixed uppercasing,
        # lowering the response should match expected
        if string.lower() != expected:
            raise NumatoGpioError(string)

    async def _query_string(self, query: str) -> str:
        """Send a query and returns the response up to the prompt as a string.

        The answer excludes the end-of-line and prompt characters.
        """
        async with self._rw_lock:
            await self._query(query)
            return await self._read_response()

    async def _read_int(self, query: str, bits: int) -> int:
        async with self._rw_lock:
            response = await self._query_string(query)
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

    async def _read_response(self, expected: str | None = None) -> str:
        """Read a response up to the terminating prompt.

        Consume the prompt (>) character from the input buffer but do not return it.
        """
        response = ""
        while (read_byte := await self._read_from_buf(1)) != ">":
            response += read_byte
        if expected and expected.lower() != response.lower():
            raise NumatoUnexpectedResponseError(
                _query := "",
                response,
                why=f"Expected response {expected!r}",
            )
        return response

    async def _read_from_buf(self, num: int) -> str:
        """Read from the internal buffer."""
        while len(self._buf) < num:
            chunk = await self._buf_queue.get()
            self._buf += chunk
        response, self._buf = self._buf[0:num], self._buf[num:]
        return response

    async def _serial_read(self, num_bytes: int) -> bytes:
        """Read from serial connection (only used by poll task and drain)."""
        if not self._reader:
            return b""
        response = await self._reader.read(num_bytes)
        return self._remove_eol(response)

    async def _read_notification(self) -> None:
        """Read a notification and call any registered callbacks.

        This method assumes that the leading '#' character has already been read.
        Notification example for a 64 port device configured to all inputs:

            # 0000000000000000 0000000000000001 FFFFFFFFFFFFFFFF
            ^ ^                ^                ^
        start previous value   new value        iodir mask
        """
        spec = await self.get_spec()
        await self._serial_read(1)
        current_value = int(await self._serial_read(spec.ports // 4), 16)
        await self._serial_read(1)
        previous_value = int(await self._serial_read(spec.ports // 4), 16)
        await self._serial_read(1)
        _ = int(await self._serial_read(spec.ports // 4), 16)  # read and discard iodir

        edges = current_value ^ previous_value

        def logic_level(port: int) -> int:
            return 1 if current_value & (1 << port) else 0

        def edge_detected(port: int) -> bool:
            return bool(edges & (1 << port))

        def edge_selected(port: int) -> bool:
            lv = logic_level(port)
            return (lv and self._edge[port] in [Edge.RISING, Edge.BOTH]) or (
                not lv and self._edge[port] in [Edge.FALLING, Edge.BOTH]
            )

        for port in range(spec.ports):
            if (
                edge_detected(port)
                and edge_selected(port)
                and (cb := self._callback[port]) is not None
            ):
                # Support both sync and async callbacks
                if inspect.iscoroutinefunction(cb):
                    await cb(port, logic_level(port))
                else:
                    cb(port, logic_level(port))

    async def _poll(self) -> None:
        """Read data and process notifications from the Numato device.

        Reads characters from the serial device and detects edge notifications
        which can interrupt the normal data at any point. Callbacks registered
        for the particular port and type of edge are processed immediately.

        This method runs as an asyncio task. It returns only when
        the serial connection is closed or an exception is caught while
        reading.
        """
        try:
            while self._writer and not self._writer.is_closing():
                b_bytes = await self._serial_read(1)
                if not b_bytes:
                    await asyncio.sleep(0)
                    continue

                b = b_bytes.decode()

                if b != "#":
                    await self._buf_queue.put(b)
                    continue

                await self._read_notification()

        except (TypeError, serial.SerialException, asyncio.CancelledError):
            if self._writer:
                with suppress(OSError):
                    self._writer.close()
                    await self._writer.wait_closed()

    def _check_port_range(self, port: int, spec: device_types.DeviceSpec) -> None:
        if port not in range(spec.ports):
            raise NumatoPortOutOfRangeError(port)

    async def _drain_ser_buffer(self) -> None:
        while await self._serial_read(DEVICE_BUFFER_SIZE):
            pass

    async def __aenter__(self) -> NumatoUsbGpioAsync:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Async context manager exit."""
        await self.cleanup()

    def __str__(self) -> str:
        """Return human readable string of the device's current state."""
        return " | ".join(
            (
                f"dev: {self.dev_file}",
                f"id: {self._id}",
                f"ver: {self._ver}",
                f"ports: {self._spec.ports if self._spec else 'unknown'}",
                f"iodir: 0x{self._iodir:0{self._hex_digits}x} ",
                f"iomask: 0x{self._iomask:0{self._hex_digits}x}",
                f"state: 0x{self._state:0{self._hex_digits}x}",
            ),
        )
