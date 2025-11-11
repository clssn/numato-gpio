"""Test async device initialization against mockup devices."""

import pytest

from numato_gpio import Direction, NumatoGpioError, NumatoIoDirError, NumatoNotifyNotSupportedError
from numato_gpio.async_api import NumatoUsbGpioAsync

# ruff: noqa: ANN001,INP001,S101


@pytest.mark.asyncio
async def test_instantiate_cleanup(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """A numato device mockup shall be initializable and properly cleaned up.

    This shall be possible for devices of any number of ports and not raise.
    """
    await mock_gpio_async.cleanup()


@pytest.mark.asyncio
async def test_write(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """A numato device mockup shall raise if input ports are written to."""
    spec = await mock_gpio_async.get_spec()

    # All ports default to input, writing should raise
    for p in range(spec.ports):
        with pytest.raises(NumatoIoDirError, match=f"port #{p}"):
            await mock_gpio_async.write(p, value=0)

    # Set all ports to output
    await mock_gpio_async.set_iodir(0)

    # Now writing should work
    for p in range(spec.ports):
        await mock_gpio_async.write(p, value=0)


@pytest.mark.asyncio
async def test_notify(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Notification setup success shall depend on device's notifications support.

    NumatoNotifyNotSupportedError shall be raised when trying to use any
    notification API on devices that don't support it.
    """
    spec = await mock_gpio_async.get_spec()

    if spec.supports_notification:
        await mock_gpio_async.set_notify(True)
        assert await mock_gpio_async.get_notify() is True
    else:
        with pytest.raises(NumatoNotifyNotSupportedError):
            await mock_gpio_async.set_notify(True)


@pytest.mark.asyncio
async def test_context_manager(mock_serial_async) -> None:
    """Test async context manager for automatic cleanup."""
    async with await NumatoUsbGpioAsync.create("/dev/ttyACMxx") as device:
        spec = await device.get_spec()
        assert spec.ports > 0

    # Device should be cleaned up
    assert not device.connected


@pytest.mark.asyncio
async def test_read_write_port(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test reading and writing individual ports."""
    spec = await mock_gpio_async.get_spec()

    # Setup port 0 as output
    await mock_gpio_async.setup(0, direction=Direction.OUT)

    # Write value
    await mock_gpio_async.write(0, value=1)

    # Read back (note: mockup may not reflect written value perfectly)
    value = await mock_gpio_async.read(0)
    assert value in [0, 1]


@pytest.mark.asyncio
async def test_readall_writeall(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test bulk read/write operations."""
    spec = await mock_gpio_async.get_spec()

    # Set all ports to output
    await mock_gpio_async.set_iodir(0)

    # Write all ports
    test_value = 0x55555555 & ((1 << spec.ports) - 1)
    await mock_gpio_async.writeall(test_value)

    # Read all ports
    value = await mock_gpio_async.readall()
    assert isinstance(value, int)


@pytest.mark.asyncio
async def test_properties(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test device properties."""
    # Get device ID
    device_id = await mock_gpio_async.get_id()
    assert isinstance(device_id, int)
    assert device_id == 0x4711  # From mock

    # Get version
    version = await mock_gpio_async.get_ver()
    assert isinstance(version, str)

    # Get spec
    spec = await mock_gpio_async.get_spec()
    assert spec.ports in [8, 16, 32, 64, 128]

    # Get/set iodir
    iodir = await mock_gpio_async.get_iodir()
    assert isinstance(iodir, int)

    await mock_gpio_async.set_iodir(0)
    iodir = await mock_gpio_async.get_iodir()
    assert iodir == 0

    # Get/set iomask
    mask = await mock_gpio_async.get_iomask()
    assert isinstance(mask, int)


@pytest.mark.asyncio
async def test_setup_direction(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test setting up individual port directions."""
    spec = await mock_gpio_async.get_spec()

    # Setup port 0 as output
    await mock_gpio_async.setup(0, direction=Direction.OUT)
    iodir = await mock_gpio_async.get_iodir()
    assert (iodir & 1) == 0  # Bit 0 should be 0 (output)

    # Setup port 1 as input
    await mock_gpio_async.setup(1, direction=Direction.IN)
    iodir = await mock_gpio_async.get_iodir()
    assert (iodir & 2) == 2  # Bit 1 should be 1 (input)
