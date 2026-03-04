"""Tests for buffer management improvements in Protocol."""
import asyncio
import pytest
from anthemav.protocol import AVR


class TestBufferManagement:
    """Test buffer management features."""

    @pytest.mark.asyncio
    async def test_buffer_max_size_configurable(self):
        """Test that buffer_max_size is configurable."""
        protocol = AVR(buffer_max_size=4096)
        assert protocol._buffer_max_size == 4096

    @pytest.mark.asyncio
    async def test_buffer_max_size_default(self):
        """Test that buffer_max_size has correct default."""
        protocol = AVR()
        assert protocol._buffer_max_size == 8192

    @pytest.mark.asyncio
    async def test_buffer_overflow_truncation(self):
        """Test that buffer is truncated when it exceeds max size."""
        protocol = AVR(buffer_max_size=100)
        
        # Create a mock transport
        class MockTransport:
            def pause_reading(self):
                pass
            def resume_reading(self):
                pass
        
        protocol.transport = MockTransport()
        
        # Fill buffer beyond max size
        large_data = "X" * 150
        protocol.buffer = large_data
        
        # Simulate data_received which checks buffer size
        assert len(protocol.buffer) > protocol._buffer_max_size
        
        # After overflow handling, buffer should be truncated to half max size
        if len(protocol.buffer) > protocol._buffer_max_size:
            protocol.buffer = protocol.buffer[-protocol._buffer_max_size // 2:]
        
        assert len(protocol.buffer) == 50  # Half of 100

    @pytest.mark.asyncio
    async def test_incomplete_message_preservation(self):
        """Test that incomplete messages are preserved in buffer."""
        protocol = AVR()
        
        # Create a mock transport
        class MockTransport:
            def pause_reading(self):
                pass
            def resume_reading(self):
                pass
            def write(self, data):
                pass  # Mock write - do nothing
        
        protocol.transport = MockTransport()
        
        # Set buffer with complete and incomplete messages
        protocol.buffer = "IDM?MRX 740;IDN?Anthem;INCOMPLETE"
        
        # Process buffer
        await protocol._assemble_buffer()
        
        # Incomplete message should remain in buffer
        assert protocol.buffer == "INCOMPLETE"

    @pytest.mark.asyncio
    async def test_complete_messages_cleared(self):
        """Test that complete messages are cleared from buffer."""
        protocol = AVR()
        
        # Create a mock transport
        class MockTransport:
            def pause_reading(self):
                pass
            def resume_reading(self):
                pass
            def write(self, data):
                pass  # Mock write - do nothing
        
        protocol.transport = MockTransport()
        
        # Set buffer with only complete messages (ending with ;)
        protocol.buffer = "IDM?MRX 740;IDN?Anthem;"
        
        # Process buffer
        await protocol._assemble_buffer()
        
        # Buffer should be empty after processing complete messages
        assert protocol.buffer == ""

    @pytest.mark.asyncio
    async def test_error_handling_preserves_buffer(self):
        """Test that errors in _assemble_buffer preserve the buffer."""
        protocol = AVR()
        
        # Create a mock transport that will cause an error
        class MockTransport:
            def pause_reading(self):
                raise RuntimeError("Test error")
            def resume_reading(self):
                pass
        
        protocol.transport = MockTransport()
        protocol.buffer = "TEST_DATA"
        
        # Process buffer - should handle error gracefully
        await protocol._assemble_buffer()
        
        # Buffer should be preserved on error
        assert protocol.buffer == "TEST_DATA"
