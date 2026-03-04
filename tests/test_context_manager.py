"""Test context manager support for Connection class."""
import asyncio
import pytest
from anthemav.connection import Connection, ConnectionState


@pytest.mark.asyncio
async def test_context_manager_cleanup():
    """Test that context manager properly cleans up resources."""
    # Create a connection without auto_reconnect to avoid actual connection attempts
    conn = await Connection.create(
        host="localhost",
        port=14999,
        auto_reconnect=False
    )
    
    # Use as context manager
    async with conn as c:
        assert c is conn
        assert c._state in [ConnectionState.DISCONNECTED, ConnectionState.CONNECTING, ConnectionState.CONNECTED]
    
    # After exiting context, connection should be closed
    assert conn._state == ConnectionState.CLOSED
    assert conn._closing is True


@pytest.mark.asyncio
async def test_context_manager_cleanup_on_exception():
    """Test that context manager cleans up even when exception occurs."""
    conn = await Connection.create(
        host="localhost",
        port=14999,
        auto_reconnect=False
    )
    
    # Use as context manager with exception
    try:
        async with conn:
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # After exiting context with exception, connection should still be closed
    assert conn._state == ConnectionState.CLOSED
    assert conn._closing is True


@pytest.mark.asyncio
async def test_context_manager_cancels_reconnect_task():
    """Test that context manager cancels pending reconnect tasks."""
    # Create connection without auto_reconnect first
    conn = await Connection.create(
        host="192.0.2.1",  # Non-routable IP to ensure connection fails
        port=14999,
        auto_reconnect=False,
        connection_timeout=0.5  # Short timeout to avoid long waits
    )
    
    # Manually create a reconnect task to simulate an active reconnection
    async def mock_reconnect():
        """Mock reconnect that sleeps indefinitely."""
        try:
            await asyncio.sleep(10)  # Long sleep to simulate ongoing reconnection
        except asyncio.CancelledError:
            raise
    
    reconnect_task = asyncio.create_task(mock_reconnect())
    conn._reconnect_task = reconnect_task
    
    # Verify task is running before context manager
    assert not reconnect_task.done()
    
    # Use as context manager
    async with conn:
        # Reconnect task should exist
        assert conn._reconnect_task is not None
    
    # After exiting, reconnect task should be cancelled and completed
    assert conn._state == ConnectionState.CLOSED
    # The task should be done (cancelled and awaited)
    assert reconnect_task.done()
    # Verify it was cancelled (will raise CancelledError when we check result)
    with pytest.raises(asyncio.CancelledError):
        reconnect_task.result()
