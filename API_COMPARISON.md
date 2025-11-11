# API Comparison: Synchronous vs Async

This document provides a side-by-side comparison of the synchronous (threaded) and asynchronous APIs for the Numato GPIO library.

## Quick Reference

| Operation | Synchronous API | Async API |
|-----------|----------------|-----------|
| **Import** | `from numato_gpio import NumatoUsbGpio` | `from numato_gpio.async_api import NumatoUsbGpioAsync` |
| **Create Device** | `device = NumatoUsbGpio("/dev/ttyACM0")` | `device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")` |
| **Get ID** | `device_id = device.id` | `device_id = await device.get_id()` |
| **Set ID** | `device.id = 5` | `await device.set_id(5)` |
| **Get Version** | `ver = device.ver` | `ver = await device.get_ver()` |
| **Get Spec** | `spec = device.spec` | `spec = await device.get_spec()` |
| **Setup Port** | `device.setup(0, direction=Direction.OUT)` | `await device.setup(0, direction=Direction.OUT)` |
| **Write Port** | `device.write(0, value=1)` | `await device.write(0, value=1)` |
| **Read Port** | `value = device.read(0)` | `value = await device.read(0)` |
| **Read ADC** | `adc = device.adc_read(0)` | `adc = await device.adc_read(0)` |
| **Read All** | `all_values = device.readall()` | `all_values = await device.readall()` |
| **Write All** | `device.writeall(0xFF)` | `await device.writeall(0xFF)` |
| **Get IODir** | `iodir = device.iodir` | `iodir = await device.get_iodir()` |
| **Set IODir** | `device.iodir = 0xFF` | `await device.set_iodir(0xFF)` |
| **Get IOMask** | `mask = device.iomask` | `mask = await device.get_iomask()` |
| **Set IOMask** | `device.iomask = 0xFF` | `await device.set_iomask(0xFF)` |
| **Get Notify** | `enabled = device.notify` | `enabled = await device.get_notify()` |
| **Set Notify** | `device.notify = True` | `await device.set_notify(True)` |
| **Add Event** | `device.add_event_detect(0, callback, Edge.BOTH)` | `await device.add_event_detect(0, callback, Edge.BOTH)` |
| **Remove Event** | `device.remove_event_detect(0)` | `device.remove_event_detect(0)` |
| **Cleanup** | `device.cleanup()` | `await device.cleanup()` |
| **Discover** | `discover()` | `await discover_async()` |
| **Cleanup All** | `cleanup()` | `await cleanup_async()` |
| **Devices Dict** | `devices` | `devices_async` |
| **Context Manager** | Not supported | `async with await NumatoUsbGpioAsync.create(...)` |

## Detailed Comparison

### 1. Initialization

#### Synchronous
```python
from numato_gpio import NumatoUsbGpio

# Direct instantiation
device = NumatoUsbGpio("/dev/ttyACM0")

# Use the device
device.setup(0, direction=Direction.OUT)

# Manual cleanup required
device.cleanup()
```

#### Async
```python
from numato_gpio.async_api import NumatoUsbGpioAsync

# Async factory method
device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

# Use the device
await device.setup(0, direction=Direction.OUT)

# Manual cleanup
await device.cleanup()

# OR use context manager for automatic cleanup
async with await NumatoUsbGpioAsync.create("/dev/ttyACM0") as device:
    await device.setup(0, direction=Direction.OUT)
    # Automatic cleanup on exit
```

### 2. Properties vs Async Methods

#### Synchronous
```python
# Properties (immediate access)
device_id = device.id
version = device.ver
spec = device.spec
iodir = device.iodir
iomask = device.iomask
notify_enabled = device.notify

# Property setters (immediate)
device.id = 5
device.iodir = 0xFF
device.iomask = 0xFF
device.notify = True
```

#### Async
```python
# Async getter methods
device_id = await device.get_id()
version = await device.get_ver()
spec = await device.get_spec()
iodir = await device.get_iodir()
iomask = await device.get_iomask()
notify_enabled = await device.get_notify()

# Async setter methods
await device.set_id(5)
await device.set_iodir(0xFF)
await device.set_iomask(0xFF)
await device.set_notify(True)
```

### 3. Event Detection Callbacks

#### Synchronous
```python
# Only synchronous callbacks supported
def my_callback(port: int, value: int):
    print(f"Port {port} = {value}")
    # Cannot use await here

device.add_event_detect(0, my_callback, Edge.BOTH)
device.notify = True
```

#### Async
```python
# Both sync and async callbacks supported
def sync_callback(port: int, value: int):
    print(f"Port {port} = {value}")

async def async_callback(port: int, value: int):
    print(f"Port {port} = {value}")
    # Can use await here!
    await some_async_function()

await device.add_event_detect(0, sync_callback, Edge.BOTH)
await device.add_event_detect(1, async_callback, Edge.RISING)
await device.set_notify(True)
```

### 4. Concurrent Operations

#### Synchronous
```python
# Sequential operations (blocking)
device1.write(0, value=1)
device2.write(0, value=1)
device3.write(0, value=1)

# To do concurrent operations, need threads
import threading

def write_device(device, port, value):
    device.write(port, value=value)

threads = [
    threading.Thread(target=write_device, args=(device1, 0, 1)),
    threading.Thread(target=write_device, args=(device2, 0, 1)),
    threading.Thread(target=write_device, args=(device3, 0, 1)),
]

for t in threads:
    t.start()
for t in threads:
    t.join()
```

#### Async
```python
# Easy concurrent operations with gather
await asyncio.gather(
    device1.write(0, value=1),
    device2.write(0, value=1),
    device3.write(0, value=1),
)

# Or with tasks
task1 = asyncio.create_task(device1.write(0, value=1))
task2 = asyncio.create_task(device2.write(0, value=1))
task3 = asyncio.create_task(device3.write(0, value=1))

await task1
await task2
await task3
```

### 5. Device Discovery

#### Synchronous
```python
from numato_gpio import discover, devices, cleanup

# Discover devices
discover()

# Access discovered devices
for dev_id, device in devices.items():
    print(f"Device {dev_id}: {device.spec.ports} ports")

# Cleanup all
cleanup()
```

#### Async
```python
from numato_gpio.async_api import discover_async, devices_async, cleanup_async

# Discover devices
await discover_async()

# Access discovered devices
for dev_id, device in devices_async.items():
    spec = await device.get_spec()
    print(f"Device {dev_id}: {spec.ports} ports")

# Cleanup all
await cleanup_async()
```

### 6. Complete Example: Blinking LED

#### Synchronous
```python
from numato_gpio import NumatoUsbGpio, Direction
import time

def blink_sync():
    device = NumatoUsbGpio("/dev/ttyACM0")
    try:
        device.setup(0, direction=Direction.OUT)

        for _ in range(10):
            device.write(0, value=1)
            time.sleep(0.5)
            device.write(0, value=0)
            time.sleep(0.5)
    finally:
        device.cleanup()

# Run it
blink_sync()
```

#### Async
```python
from numato_gpio.async_api import NumatoUsbGpioAsync
from numato_gpio import Direction
import asyncio

async def blink_async():
    async with await NumatoUsbGpioAsync.create("/dev/ttyACM0") as device:
        await device.setup(0, direction=Direction.OUT)

        for _ in range(10):
            await device.write(0, value=1)
            await asyncio.sleep(0.5)
            await device.write(0, value=0)
            await asyncio.sleep(0.5)

# Run it
asyncio.run(blink_async())
```

### 7. Multiple Concurrent Blinks

#### Synchronous
```python
import threading
import time

def blink_port(device, port, interval, count):
    for _ in range(count):
        device.write(port, value=1)
        time.sleep(interval)
        device.write(port, value=0)
        time.sleep(interval)

device = NumatoUsbGpio("/dev/ttyACM0")
try:
    device.setup(0, direction=Direction.OUT)
    device.setup(1, direction=Direction.OUT)

    t1 = threading.Thread(target=blink_port, args=(device, 0, 0.5, 10))
    t2 = threading.Thread(target=blink_port, args=(device, 1, 0.3, 15))

    t1.start()
    t2.start()
    t1.join()
    t2.join()
finally:
    device.cleanup()
```

#### Async
```python
import asyncio

async def blink_port(device, port, interval, count):
    for _ in range(count):
        await device.write(port, value=1)
        await asyncio.sleep(interval)
        await device.write(port, value=0)
        await asyncio.sleep(interval)

async def main():
    async with await NumatoUsbGpioAsync.create("/dev/ttyACM0") as device:
        await device.setup(0, direction=Direction.OUT)
        await device.setup(1, direction=Direction.OUT)

        # Run both blinks concurrently
        await asyncio.gather(
            blink_port(device, 0, 0.5, 10),
            blink_port(device, 1, 0.3, 15),
        )

asyncio.run(main())
```

## When to Use Each API

### Use Synchronous API When:
- You have a simple, sequential workflow
- You're not using async frameworks
- You prefer simpler, more traditional Python code
- You don't need concurrent operations
- Your application doesn't use asyncio

### Use Async API When:
- You need concurrent operations on multiple devices/ports
- You're using async frameworks (FastAPI, aiohttp, etc.)
- You need non-blocking I/O
- You want async callbacks for events
- You're building event-driven applications
- You need better integration with other async code

## Performance Characteristics

| Aspect | Synchronous | Async |
|--------|-------------|-------|
| **Single Operation** | Slightly faster (less overhead) | Slightly slower (asyncio overhead) |
| **Concurrent Operations** | Uses threads (OS overhead) | Uses asyncio (efficient) |
| **Memory Usage** | Higher (thread stacks) | Lower (coroutines) |
| **Scalability** | Limited by thread count | Excellent (many coroutines) |
| **CPU Efficiency** | Context switching overhead | Cooperative multitasking |
| **Best For** | Simple, sequential tasks | Concurrent, I/O-bound tasks |

## Migration Checklist

To migrate from sync to async:

1. ✅ Change imports
   - `NumatoUsbGpio` → `NumatoUsbGpioAsync`
   - `discover` → `discover_async`
   - `devices` → `devices_async`

2. ✅ Add `async`/`await` keywords
   - All method calls need `await`
   - Function definitions need `async def`

3. ✅ Change property access to method calls
   - `device.id` → `await device.get_id()`
   - `device.ver` → `await device.get_ver()`

4. ✅ Update initialization
   - `NumatoUsbGpio(path)` → `await NumatoUsbGpioAsync.create(path)`

5. ✅ Consider using context managers
   - `async with await NumatoUsbGpioAsync.create(...):`

6. ✅ Replace `time.sleep()` with `await asyncio.sleep()`

7. ✅ Replace `threading` with `asyncio` patterns

8. ✅ Wrap main code in async function and run with `asyncio.run()`

## Common Pitfalls

### Synchronous API
- Forgetting to call `cleanup()` (no context manager)
- Thread safety issues when sharing device objects
- Blocking the main thread with long operations

### Async API
- Forgetting `await` keyword (will get coroutine objects)
- Using `time.sleep()` instead of `await asyncio.sleep()`
- Calling sync blocking functions in async context
- Forgetting to use `await` with the `create()` factory method

## See Also

- `ASYNC_API.md` - Detailed async API documentation
- `examples/async_example.py` - Comprehensive async examples
- Main README - General library documentation
