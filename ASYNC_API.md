# Async API for Numato GPIO

This document describes the asynchronous API for Numato USB GPIO devices, which provides a non-blocking alternative to the synchronous/multithreaded API.

## Overview

The async API (`numato_gpio.async_api`) uses Python's `asyncio` library and `pyserial-asyncio` to provide non-blocking I/O operations for Numato GPIO devices. This is particularly useful for:

- Applications that need to handle multiple devices concurrently
- Integration with async frameworks (aiohttp, FastAPI, etc.)
- Event-driven applications with GPIO event detection
- Applications that need to perform other async operations while waiting for GPIO operations

## Key Differences from Synchronous API

| Feature | Synchronous API | Async API |
|---------|----------------|-----------|
| **I/O Model** | Blocking with background polling thread | Non-blocking with asyncio tasks |
| **Concurrency** | Threading-based (`threading.RLock`) | Asyncio-based (`asyncio.Lock`) |
| **Method Calls** | `device.read(port)` | `await device.read(port)` |
| **Properties** | `device.id`, `device.ver` | `await device.get_id()`, `await device.get_ver()` |
| **Initialization** | `device = NumatoUsbGpio(path)` | `device = await NumatoUsbGpioAsync.create(path)` |
| **Context Manager** | Not supported | `async with await NumatoUsbGpioAsync.create(...)` |
| **Callbacks** | Sync only | Sync and async both supported |
| **Discovery** | `discover()` | `await discover_async()` |
| **Device Registry** | `devices` dict | `devices_async` dict |

## Installation

The async API requires `pyserial-asyncio`:

```bash
pip install numato-gpio[async]
# or
pip install numato-gpio pyserial-asyncio
```

## Basic Usage

### Simple Example

```python
import asyncio
from numato_gpio.async_api import NumatoUsbGpioAsync
from numato_gpio import Direction

async def main():
    # Create device connection
    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        # Setup port as output
        await device.setup(0, direction=Direction.OUT)

        # Write value
        await device.write(0, value=1)

        # Setup port as input
        await device.setup(1, direction=Direction.IN)

        # Read value
        value = await device.read(1)
        print(f"Port 1: {value}")

    finally:
        await device.cleanup()

asyncio.run(main())
```

### Using Context Manager

```python
async def main():
    async with await NumatoUsbGpioAsync.create("/dev/ttyACM0") as device:
        await device.setup(0, direction=Direction.OUT)
        await device.write(0, value=1)
        # Automatic cleanup on exit
```

## API Reference

### Class: NumatoUsbGpioAsync

#### Factory Method

- **`await NumatoUsbGpioAsync.create(device="/dev/ttyACM0")`**
  - Creates and initializes a device connection
  - Returns: `NumatoUsbGpioAsync` instance
  - Raises: `NumatoGpioError` if device doesn't respond

#### Properties (Async Methods)

- **`await device.get_id()`** - Get device ID
- **`await device.set_id(new_id)`** - Set device ID
- **`await device.get_ver()`** - Get firmware version
- **`await device.get_spec()`** - Get device specification
- **`await device.get_notify()`** - Get notification enable status
- **`await device.set_notify(enable)`** - Enable/disable notifications
- **`await device.get_iodir()`** - Get I/O direction mask
- **`await device.set_iodir(direction)`** - Set I/O direction mask
- **`await device.get_iomask()`** - Get I/O protection mask
- **`await device.set_iomask(mask)`** - Set I/O protection mask
- **`device.connected`** - Check if connected (property, not async)

#### Port Operations

- **`await device.setup(port, *, direction)`**
  - Configure a single port as input or output
  - Args: `port` (int), `direction` (Direction.IN or Direction.OUT)

- **`await device.write(port, *, value)`**
  - Write logic level to a port
  - Args: `port` (int), `value` (0/False or 1/True)
  - Raises: `NumatoIoDirError` if port is configured as input

- **`await device.read(port)`**
  - Read logic level from a port
  - Returns: 0 or 1

- **`await device.adc_read(adc_port)`**
  - Read analog value from ADC-capable port
  - Returns: int (0-1023 for 10-bit ADC)
  - Raises: `NumatoAdcPortError` if port doesn't have ADC

#### Bulk Operations

- **`await device.readall()`**
  - Read all ports at once
  - Returns: int (bit vector)

- **`await device.writeall(bits)`**
  - Write all output ports at once
  - Args: `bits` (int as bit vector)

#### Event Detection

- **`await device.add_event_detect(port, callback, edge=Edge.BOTH)`**
  - Register callback for port events
  - Args:
    - `port` (int)
    - `callback` - Can be sync or async function with signature `(port: int, value: int) -> None`
    - `edge` - Edge.RISING, Edge.FALLING, or Edge.BOTH
  - Note: Must call `await device.set_notify(True)` to enable

- **`device.remove_event_detect(port)`**
  - Remove event callback for port (not async)

#### Cleanup

- **`await device.cleanup()`**
  - Reset all ports to input and close connection
  - Called automatically when using context manager

### Module Functions

- **`await discover_async(dev_files=DEFAULT_DEVICES)`**
  - Scan device files for Numato devices
  - Populates `devices_async` dict with device_id -> device mapping

- **`await cleanup_async()`**
  - Cleanup all discovered devices

### Module Variables

- **`devices_async`** - Dict of discovered devices (keyed by device ID)

## Advanced Usage

### Concurrent Operations

```python
async def main():
    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        # Setup ports
        await device.setup(0, direction=Direction.OUT)
        await device.setup(1, direction=Direction.OUT)

        # Blink multiple ports concurrently
        async def blink(port, interval, count):
            for _ in range(count):
                await device.write(port, value=1)
                await asyncio.sleep(interval)
                await device.write(port, value=0)
                await asyncio.sleep(interval)

        # Run both blinks at the same time
        await asyncio.gather(
            blink(0, 0.5, 10),
            blink(1, 0.3, 15),
        )
    finally:
        await device.cleanup()
```

### Event Detection with Async Callbacks

```python
async def main():
    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        # Setup input port
        await device.setup(2, direction=Direction.IN)

        # Define async callback (can do async operations)
        async def on_change(port, value):
            print(f"Port {port} changed to {value}")
            # Can await here
            await asyncio.sleep(0.1)
            # Do async database write, HTTP request, etc.

        # Register callback and enable
        await device.add_event_detect(2, on_change, edge=Edge.BOTH)
        await device.set_notify(True)

        # Wait for events
        await asyncio.sleep(60)

        # Cleanup
        await device.set_notify(False)
        device.remove_event_detect(2)
    finally:
        await device.cleanup()
```

### Multiple Devices

```python
async def main():
    # Discover all devices
    await discover_async()

    # Work with all devices concurrently
    async def read_device(device):
        value = await device.readall()
        return value

    results = await asyncio.gather(
        *[read_device(dev) for dev in devices_async.values()]
    )

    for (dev_id, device), value in zip(devices_async.items(), results):
        print(f"Device {dev_id}: 0x{value:x}")

    # Cleanup all
    await cleanup_async()
```

### Integration with Web Framework (FastAPI)

```python
from fastapi import FastAPI
from numato_gpio.async_api import NumatoUsbGpioAsync
from numato_gpio import Direction

app = FastAPI()
device = None

@app.on_event("startup")
async def startup():
    global device
    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")
    await device.setup(0, direction=Direction.OUT)

@app.on_event("shutdown")
async def shutdown():
    if device:
        await device.cleanup()

@app.post("/gpio/{port}/write/{value}")
async def write_port(port: int, value: int):
    await device.write(port, value=value)
    return {"status": "ok", "port": port, "value": value}

@app.get("/gpio/{port}/read")
async def read_port(port: int):
    value = await device.read(port)
    return {"port": port, "value": value}
```

## Performance Considerations

1. **Concurrent Operations**: The async API allows true concurrency for I/O operations across multiple devices or ports
2. **Event Loop**: All operations run in the event loop - avoid blocking operations in callbacks
3. **Callbacks**: Async callbacks are supported and can perform async operations without blocking
4. **Lock Contention**: Uses asyncio.Lock instead of threading locks, more efficient for async code

## Error Handling

All exceptions from the synchronous API are re-used:

- `NumatoGpioError` - Base exception
- `NumatoIoDirError` - Wrong port direction
- `NumatoAdcPortError` - Invalid ADC port
- `NumatoSerialIoError` - Serial communication error
- `NumatoPortOutOfRangeError` - Port out of range
- etc.

```python
async def main():
    try:
        device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")
        await device.write(0, value=1)  # May raise NumatoIoDirError
    except NumatoIoDirError as e:
        print(f"Port direction error: {e}")
    except NumatoGpioError as e:
        print(f"GPIO error: {e}")
    finally:
        if device:
            await device.cleanup()
```

## Migration Guide

### From Synchronous to Async

1. **Add async/await keywords**:
   ```python
   # Before
   device = NumatoUsbGpio("/dev/ttyACM0")
   value = device.read(0)

   # After
   device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")
   value = await device.read(0)
   ```

2. **Change property access to method calls**:
   ```python
   # Before
   dev_id = device.id
   version = device.ver

   # After
   dev_id = await device.get_id()
   version = await device.get_ver()
   ```

3. **Update imports**:
   ```python
   # Before
   from numato_gpio import NumatoUsbGpio, discover, devices

   # After
   from numato_gpio.async_api import NumatoUsbGpioAsync, discover_async, devices_async
   from numato_gpio import Direction, Edge  # These are still imported from main module
   ```

4. **Wrap in async function and run with asyncio**:
   ```python
   async def main():
       # Your code here
       pass

   asyncio.run(main())
   ```

## Examples

See `examples/async_example.py` for comprehensive examples including:
- Basic port operations
- Context managers
- Event detection
- Concurrent operations
- ADC reading
- Device discovery
- Bulk operations

## Limitations

1. The async API requires Linux (serial device files)
2. Requires Python 3.9+ (same as synchronous API)
3. pyserial-asyncio must be installed

## See Also

- Main README for general information
- Examples directory for code samples
- API documentation for detailed method descriptions
