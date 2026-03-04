"""Property-based tests for model registry."""
from hypothesis import given, settings, strategies as st
from anthemav.models import ModelRegistry
from anthemav.models.base import BaseModel
from typing import Dict, List


class MockModel(BaseModel):
    """Mock model implementation for testing."""

    def __init__(self, series: str):
        """Initialize mock model with a series identifier."""
        self._series = series

    def get_model_series(self) -> str:
        """Return the model series identifier."""
        return self._series

    def get_zone_count(self, model_name: str) -> int:
        """Return the number of zones supported by this model."""
        return 2

    def get_available_input_numbers(self, model_name: str) -> List[int]:
        """Return list of available input numbers."""
        return []

    def get_commands_to_query(self) -> List[str]:
        """Return list of commands to query during initialization."""
        return ["IDN"]

    def get_commands_to_ignore(self) -> List[str]:
        """Return list of commands to ignore for this model."""
        return []

    def get_alm_number_mapping(self) -> Dict[str, int]:
        """Return audio listening mode name to number mapping."""
        return {"None": 0}

    def get_alm_restricted_models(self) -> List[str]:
        """Return list of model names with restricted listening modes."""
        return []

    def supports_audio_listening_mode(self) -> bool:
        """Return True if model supports audio listening modes."""
        return True

    def supports_arc(self) -> bool:
        """Return True if model supports Anthem Room Correction."""
        return True

    def supports_profile(self) -> bool:
        """Return True if model supports sound profiles."""
        return True

    def get_mac_address_command(self) -> str:
        """Return the command to query MAC address."""
        return "IDN"

    def get_volume_command_format(self, zone: int) -> str:
        """Return volume command format."""
        return "VOL"

    def format_input_query(self, input_number: int) -> str:
        """Format input name query command for this model."""
        return f"ISN{input_number:02d}"

    def format_arc_command(self, zone: int, input_number: int) -> str:
        """Format ARC query/set command for this model."""
        return f"Z{zone}ARC"

    def on_model_detected(self, avr) -> None:
        """Called when model is detected."""
        pass

    def parse_message(self, message: str):
        """Parse a message in this model's format."""
        from anthemav.parser import ParsedMessage
        if not message:
            return None
        parsed = ParsedMessage()
        parsed.command = "TEST"
        parsed.value = message
        parsed.input_number = 0
        parsed.zone = 0
        return parsed

    def format_message(self, parsed) -> str:
        """Format a parsed message back to string."""
        if not parsed:
            return ""
        return f"{parsed.command}{parsed.value}"


@settings(max_examples=100)
@given(model_name=st.one_of(
    # x40 series patterns
    st.sampled_from(["MRX 540", "MRX 740", "MRX 1140", "AVM 70", "AVM 90"]),
    st.text(min_size=1, max_size=50).filter(lambda s: any(x in s for x in ["40", "70", "90"])),
    # MDX series patterns
    st.sampled_from(["MDX-8", "MDX-16", "MDA-8", "MDA-16"]),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDX" in s or "MDA" in s),
    # x20 series patterns (default for anything else)
    st.sampled_from(["MRX 520", "MRX 720", "MRX 1120", "AVM 60"]),
    st.text(min_size=1, max_size=50).filter(
        lambda s: s and s != "Unknown Model" and 
        not any(x in s for x in ["40", "70", "90", "MDX", "MDA"])
    )
))
def test_model_detection_correctness(model_name):
    """Feature: anthemav-refactoring, Property 1: Model Detection Correctness.
    
    For any valid Anthem model identifier string (containing "40", "70", "90" for x40;
    "MDX" or "MDA" for MDX; or other strings for x20), the model registry should detect
    and return the correct model implementation corresponding to that identifier.
    
    Validates: Requirements 1.1, 2.3
    """
    # Create a registry with mock models registered
    registry = ModelRegistry()
    x20_model = MockModel("x20")
    x40_model = MockModel("x40")
    mdx_model = MockModel("mdx")
    
    registry.register(x20_model)
    registry.register(x40_model)
    registry.register(mdx_model)
    
    # Detect the model based on the model name
    detected_model = registry.detect_model(model_name)
    
    # Verify a model was detected (should never be None for valid model names)
    assert detected_model is not None, \
        f"Model detection failed: no model detected for '{model_name}'"
    
    # Verify the correct model series was detected
    detected_series = detected_model.get_model_series()
    
    # Determine expected series based on model name patterns
    if any(x in model_name for x in ["40", "70", "90"]):
        expected_series = "x40"
    elif "MDX" in model_name or "MDA" in model_name:
        expected_series = "mdx"
    else:
        expected_series = "x20"
    
    assert detected_series == expected_series, \
        f"Model detection incorrect: expected '{expected_series}' for '{model_name}', " \
        f"but got '{detected_series}'"
    
    # Verify the detected model is the correct instance
    if expected_series == "x40":
        assert detected_model is x40_model, \
            f"Expected x40 model instance for '{model_name}'"
    elif expected_series == "mdx":
        assert detected_model is mdx_model, \
            f"Expected mdx model instance for '{model_name}'"
    else:
        assert detected_model is x20_model, \
            f"Expected x20 model instance for '{model_name}'"


@settings(max_examples=100)
@given(series=st.text(min_size=1, max_size=20, alphabet=st.characters(
    whitelist_categories=('Lu', 'Ll', 'Nd'),
    whitelist_characters='-_'
)))
def test_model_registry_round_trip(series):
    """Feature: anthemav-refactoring, Property 2: Model Registry Round-Trip.
    
    For any model implementation registered in the registry, retrieving it by
    its series identifier should return the same model instance that was registered.
    
    Validates: Requirements 2.1
    """
    # Create a fresh registry for each test
    registry = ModelRegistry()
    
    # Create a mock model with the generated series identifier
    model = MockModel(series)
    
    # Register the model
    registry.register(model)
    
    # Retrieve the model by its series identifier
    retrieved_model = registry.get_model(series)
    
    # Verify the retrieved model is the same instance
    assert retrieved_model is model, \
        f"Registry round-trip failed: registered {model} but retrieved {retrieved_model}"
    
    # Verify the series identifier matches
    assert retrieved_model.get_model_series() == series, \
        f"Series mismatch: expected {series}, got {retrieved_model.get_model_series()}"
