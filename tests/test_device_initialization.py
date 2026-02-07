"""Tests for device initialization enhancements (Task 14)."""
import pytest
from anthemav.protocol import AVR, EMPTY_MAC, UNKNOWN_MODEL
from anthemav.device_error import DeviceError


class TestDeviceInitialization:
    """Test device initialization timeout and validation."""

    @pytest.mark.asyncio
    async def test_wait_for_device_initialised_timeout(self):
        """Test that wait_for_device_initialised raises DeviceError on timeout."""
        avr = AVR()

        # Should timeout since device is not initialized
        with pytest.raises(DeviceError) as exc_info:
            await avr.wait_for_device_initialised(timeout=0.1)

        # Verify error message contains timeout information
        assert "timed out" in str(exc_info.value).lower()
        assert "0.1" in str(exc_info.value)

        # Verify error context
        assert exc_info.value.context["timeout"] == 0.1

    @pytest.mark.asyncio
    async def test_wait_for_device_initialised_incomplete_mac(self):
        """Test that wait_for_device_initialised raises DeviceError for empty MAC."""
        avr = AVR()

        # Set model but leave MAC as EMPTY_MAC
        avr._IDM = "MRX 520"
        avr._IDN = EMPTY_MAC

        # Manually set the event to simulate receiving data
        avr._deviceinfo_received.set()

        # Should raise DeviceError due to empty MAC
        with pytest.raises(DeviceError) as exc_info:
            await avr.wait_for_device_initialised(timeout=1.0)

        # Verify error message
        assert "incomplete" in str(exc_info.value).lower()
        assert exc_info.value.context["macaddress"] == EMPTY_MAC

    @pytest.mark.asyncio
    async def test_wait_for_device_initialised_unknown_model(self):
        """Test that wait_for_device_initialised raises DeviceError for unknown model."""
        avr = AVR()

        # Set MAC but leave model as UNKNOWN_MODEL
        avr._IDM = UNKNOWN_MODEL
        avr._IDN = "AA:BB:CC:DD:EE:FF"

        # Manually set the event
        avr._deviceinfo_received.set()

        # Should raise DeviceError due to unknown model
        with pytest.raises(DeviceError) as exc_info:
            await avr.wait_for_device_initialised(timeout=1.0)

        # Verify error message
        assert "incomplete" in str(exc_info.value).lower()
        assert exc_info.value.context["model"] == UNKNOWN_MODEL

    @pytest.mark.asyncio
    async def test_wait_for_device_initialised_success(self):
        """Test that wait_for_device_initialised succeeds with valid data."""
        avr = AVR()

        # Set valid model and MAC
        avr._IDM = "MRX 520"
        avr._IDN = "AA:BB:CC:DD:EE:FF"

        # Manually set the event
        avr._deviceinfo_received.set()

        # Should succeed without raising
        await avr.wait_for_device_initialised(timeout=1.0)

    def test_is_initialized_returns_false_initially(self):
        """Test that is_initialized returns False before initialization."""
        avr = AVR()
        assert avr.is_initialized() is False

    def test_is_initialized_returns_true_after_event_set(self):
        """Test that is_initialized returns True after event is set."""
        avr = AVR()
        avr._deviceinfo_received.set()
        assert avr.is_initialized() is True

    def test_set_device_initialised_requires_valid_model(self):
        """Test that _set_device_initialised only sets event with valid model."""
        avr = AVR()

        # Set valid MAC but invalid model
        avr._IDM = UNKNOWN_MODEL
        avr._IDN = "AA:BB:CC:DD:EE:FF"
        avr._model_series = "x20"

        # Should not set the event
        avr._set_device_initialised()
        assert avr.is_initialized() is False

    def test_set_device_initialised_requires_valid_mac(self):
        """Test that _set_device_initialised only sets event with valid MAC."""
        avr = AVR()

        # Set valid model but invalid MAC
        avr._IDM = "MRX 520"
        avr._IDN = EMPTY_MAC
        avr._model_series = "x20"

        # Should not set the event
        avr._set_device_initialised()
        assert avr.is_initialized() is False

    def test_set_device_initialised_success(self):
        """Test that _set_device_initialised sets event with valid data."""
        avr = AVR()

        # Set valid model and MAC
        avr._IDM = "MRX 520"
        avr._IDN = "AA:BB:CC:DD:EE:FF"
        avr._model_series = "x20"

        # Should set the event
        avr._set_device_initialised()
        assert avr.is_initialized() is True

    def test_device_error_with_context(self):
        """Test that DeviceError stores message and context correctly."""
        error = DeviceError(
            message="Test error",
            context={"timeout": 10.0, "model": "MRX 520"}
        )

        assert error.message == "Test error"
        assert error.context["timeout"] == 10.0
        assert error.context["model"] == "MRX 520"
        assert str(error) == "Test error"

    def test_device_error_default_values(self):
        """Test that DeviceError has sensible defaults."""
        error = DeviceError()

        assert error.message == "Device initialization failed"
        assert error.context == {}
        assert str(error) == "Device initialization failed"
