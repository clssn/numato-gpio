"""Test async event detection and notifications."""

import asyncio

import pytest

from numato_gpio import Direction, Edge, NumatoNotifyNotSupportedError
from numato_gpio.async_api import NumatoUsbGpioAsync

# ruff: noqa: ANN001,INP001,S101


@pytest.mark.asyncio
async def test_add_remove_event_detect(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test adding and removing event detection callbacks."""
    spec = await mock_gpio_async.get_spec()

    if not spec.supports_notification:
        pytest.skip("Device doesn't support notifications")

    callback_called = False

    def sync_callback(port: int, value: int):
        nonlocal callback_called
        callback_called = True

    # Setup port as input
    await mock_gpio_async.setup(0, direction=Direction.IN)

    # Add event detection
    await mock_gpio_async.add_event_detect(0, sync_callback, edge=Edge.BOTH)

    # Remove event detection
    mock_gpio_async.remove_event_detect(0)


@pytest.mark.asyncio
async def test_async_callback(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test async callback for event detection."""
    spec = await mock_gpio_async.get_spec()

    if not spec.supports_notification:
        pytest.skip("Device doesn't support notifications")

    callback_called = False
    callback_value = None

    async def async_callback(port: int, value: int):
        nonlocal callback_called, callback_value
        callback_called = True
        callback_value = value
        await asyncio.sleep(0.01)  # Simulate async operation

    # Setup port as input
    await mock_gpio_async.setup(0, direction=Direction.IN)

    # Add async event detection
    await mock_gpio_async.add_event_detect(0, async_callback, edge=Edge.BOTH)

    # Note: In a real test with hardware, we'd wait for an actual event
    # In the mock, we can't easily trigger events, so we just verify setup works


@pytest.mark.asyncio
async def test_sync_callback(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test sync callback for event detection."""
    spec = await mock_gpio_async.get_spec()

    if not spec.supports_notification:
        pytest.skip("Device doesn't support notifications")

    callback_called = False

    def sync_callback(port: int, value: int):
        nonlocal callback_called
        callback_called = True

    # Setup port as input
    await mock_gpio_async.setup(0, direction=Direction.IN)

    # Add sync event detection
    await mock_gpio_async.add_event_detect(0, sync_callback, edge=Edge.RISING)


@pytest.mark.asyncio
async def test_edge_types(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test different edge detection types."""
    spec = await mock_gpio_async.get_spec()

    if not spec.supports_notification:
        pytest.skip("Device doesn't support notifications")

    def callback(port: int, value: int):
        pass

    # Setup port as input
    await mock_gpio_async.setup(0, direction=Direction.IN)

    # Test RISING edge
    await mock_gpio_async.add_event_detect(0, callback, edge=Edge.RISING)
    mock_gpio_async.remove_event_detect(0)

    # Test FALLING edge
    await mock_gpio_async.add_event_detect(0, callback, edge=Edge.FALLING)
    mock_gpio_async.remove_event_detect(0)

    # Test BOTH edges
    await mock_gpio_async.add_event_detect(0, callback, edge=Edge.BOTH)
    mock_gpio_async.remove_event_detect(0)


@pytest.mark.asyncio
async def test_notify_not_supported(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test that notification APIs raise error on unsupported devices."""
    spec = await mock_gpio_async.get_spec()

    if spec.supports_notification:
        pytest.skip("Device supports notifications")

    def callback(port: int, value: int):
        pass

    # Should raise error when trying to add event detect
    with pytest.raises(NumatoNotifyNotSupportedError):
        await mock_gpio_async.add_event_detect(0, callback, edge=Edge.BOTH)

    # Should raise error when trying to enable notifications
    with pytest.raises(NumatoNotifyNotSupportedError):
        await mock_gpio_async.set_notify(True)


@pytest.mark.asyncio
async def test_multiple_callbacks(mock_gpio_async: NumatoUsbGpioAsync) -> None:
    """Test multiple callbacks on different ports."""
    spec = await mock_gpio_async.get_spec()

    if not spec.supports_notification:
        pytest.skip("Device doesn't support notifications")

    if spec.ports < 4:
        pytest.skip("Need at least 4 ports for this test")

    callbacks_called = [False, False, False]

    def callback_0(port: int, value: int):
        callbacks_called[0] = True

    def callback_1(port: int, value: int):
        callbacks_called[1] = True

    async def callback_2(port: int, value: int):
        callbacks_called[2] = True
        await asyncio.sleep(0.01)

    # Setup ports as inputs
    await mock_gpio_async.setup(0, direction=Direction.IN)
    await mock_gpio_async.setup(1, direction=Direction.IN)
    await mock_gpio_async.setup(2, direction=Direction.IN)

    # Add event detection on multiple ports
    await mock_gpio_async.add_event_detect(0, callback_0, edge=Edge.BOTH)
    await mock_gpio_async.add_event_detect(1, callback_1, edge=Edge.RISING)
    await mock_gpio_async.add_event_detect(2, callback_2, edge=Edge.FALLING)

    # Remove all
    mock_gpio_async.remove_event_detect(0)
    mock_gpio_async.remove_event_detect(1)
    mock_gpio_async.remove_event_detect(2)
