"""Example usage of the async Numato GPIO API.

This demonstrates the key features of the async API including:
- Device discovery
- Port setup and I/O operations
- Event detection with callbacks
- Async context managers
- Multiple concurrent operations
"""

import asyncio
from numato_gpio.async_api import NumatoUsbGpioAsync, discover_async, devices_async
from numato_gpio import Direction, Edge


async def basic_example():
    """Basic example: setup a port and read/write values."""
    print("\n=== Basic Example ===")

    # Create a device connection
    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        # Setup port 0 as output
        await device.setup(0, direction=Direction.OUT)

        # Write high
        await device.write(0, value=1)
        print("Port 0 set to HIGH")

        # Setup port 1 as input
        await device.setup(1, direction=Direction.IN)

        # Read value
        value = await device.read(1)
        print(f"Port 1 value: {value}")

    finally:
        # Cleanup
        await device.cleanup()


async def context_manager_example():
    """Example using async context manager for automatic cleanup."""
    print("\n=== Context Manager Example ===")

    async with await NumatoUsbGpioAsync.create("/dev/ttyACM0") as device:
        # Get device info
        dev_id = await device.get_id()
        version = await device.get_ver()
        spec = await device.get_spec()

        print(f"Device ID: {dev_id}")
        print(f"Version: {version}")
        print(f"Ports: {spec.ports}")

        # Use the device...
        await device.setup(0, direction=Direction.OUT)
        await device.write(0, value=1)

    # Device is automatically cleaned up


async def event_detection_example():
    """Example with event detection and callbacks."""
    print("\n=== Event Detection Example ===")

    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        # Setup port 2 as input
        await device.setup(2, direction=Direction.IN)

        # Define an async callback
        async def on_port_change(port: int, value: int):
            print(f"Async callback: Port {port} changed to {value}")
            # Can do async operations here
            await asyncio.sleep(0.1)
            print(f"Finished processing port {port}")

        # Define a sync callback
        def on_port_change_sync(port: int, value: int):
            print(f"Sync callback: Port {port} changed to {value}")

        # Register callbacks (both async and sync are supported)
        await device.add_event_detect(2, on_port_change, edge=Edge.BOTH)
        await device.add_event_detect(3, on_port_change_sync, edge=Edge.RISING)

        # Enable notifications
        await device.set_notify(True)

        print("Listening for events on ports 2 and 3...")
        print("Change port states to trigger callbacks")

        # Wait for events (in real application, you'd do other work)
        await asyncio.sleep(30)

        # Disable notifications
        await device.set_notify(False)

        # Remove event detection
        device.remove_event_detect(2)
        device.remove_event_detect(3)

    finally:
        await device.cleanup()


async def discovery_example():
    """Example using device discovery."""
    print("\n=== Discovery Example ===")

    # Discover all connected devices
    await discover_async()

    print(f"Found {len(devices_async)} device(s)")

    # Work with discovered devices
    for dev_id, device in devices_async.items():
        spec = await device.get_spec()
        print(f"Device {dev_id}: {spec.ports} ports")


async def concurrent_operations_example():
    """Example of concurrent operations on multiple ports."""
    print("\n=== Concurrent Operations Example ===")

    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        # Setup multiple ports
        await device.setup(0, direction=Direction.OUT)
        await device.setup(1, direction=Direction.OUT)
        await device.setup(2, direction=Direction.OUT)

        # Define an async task for blinking a port
        async def blink_port(port: int, interval: float, count: int):
            for i in range(count):
                await device.write(port, value=1)
                await asyncio.sleep(interval)
                await device.write(port, value=0)
                await asyncio.sleep(interval)
            print(f"Port {port} blink complete")

        # Run multiple blink tasks concurrently
        await asyncio.gather(
            blink_port(0, 0.5, 5),  # Port 0: 0.5s interval, 5 blinks
            blink_port(1, 0.3, 8),  # Port 1: 0.3s interval, 8 blinks
            blink_port(2, 0.7, 3),  # Port 2: 0.7s interval, 3 blinks
        )

        print("All blink tasks complete!")

    finally:
        await device.cleanup()


async def adc_example():
    """Example reading analog values from ADC ports."""
    print("\n=== ADC Example ===")

    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        spec = await device.get_spec()

        if not spec.adc_ports:
            print("This device doesn't have ADC ports")
            return

        print(f"ADC ports available: {list(spec.adc_ports.keys())}")

        # Read from first ADC port
        adc_port = list(spec.adc_ports.keys())[0]
        value = await device.adc_read(adc_port)
        voltage = (value / (2**spec.adc_resolution_bits)) * 3.3  # Assuming 3.3V ref
        print(f"ADC port {adc_port}: {value} (≈{voltage:.2f}V)")

        # Continuous reading
        print("\nReading ADC values for 10 seconds...")
        for _ in range(10):
            value = await device.adc_read(adc_port)
            print(f"ADC value: {value}", end="\r")
            await asyncio.sleep(1)
        print()

    finally:
        await device.cleanup()


async def bulk_operations_example():
    """Example using bulk read/write operations."""
    print("\n=== Bulk Operations Example ===")

    device = await NumatoUsbGpioAsync.create("/dev/ttyACM0")

    try:
        spec = await device.get_spec()

        # Set all ports as outputs
        await device.set_iodir(0)

        # Write a pattern to all ports (e.g., alternating bits)
        pattern = 0xAAAAAAAA & ((1 << spec.ports) - 1)
        await device.writeall(pattern)
        print(f"Written pattern: 0x{pattern:0{spec.ports//4}x}")

        # Read all ports
        values = await device.readall()
        print(f"Read values: 0x{values:0{spec.ports//4}x}")

        # Shift pattern
        for i in range(8):
            pattern = ((pattern << 1) | (pattern >> (spec.ports - 1))) & (
                (1 << spec.ports) - 1
            )
            await device.writeall(pattern)
            await asyncio.sleep(0.2)
            print(f"Pattern {i+1}: 0x{pattern:0{spec.ports//4}x}")

    finally:
        await device.cleanup()


async def main():
    """Run all examples."""
    print("Numato GPIO Async API Examples")
    print("=" * 50)

    # Choose which examples to run
    examples = [
        ("Basic", basic_example),
        ("Context Manager", context_manager_example),
        ("Discovery", discovery_example),
        ("ADC", adc_example),
        ("Bulk Operations", bulk_operations_example),
        ("Concurrent Operations", concurrent_operations_example),
        # ("Event Detection", event_detection_example),  # Uncomment to test
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"Error in {name} example: {e}")

        await asyncio.sleep(1)  # Brief pause between examples

    print("\n" + "=" * 50)
    print("Examples complete!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
