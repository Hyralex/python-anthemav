"""Property-based tests for model configuration."""
from hypothesis import given, settings, strategies as st
from anthemav.models import ModelRegistry
from anthemav.models.x20 import X20Model
from anthemav.models.x40 import X40Model
from anthemav.models.mdx import MDXModel


@settings(max_examples=100)
@given(model_name=st.one_of(
    # x20 series models - should return 2 zones
    st.sampled_from(["MRX 520", "MRX 720", "MRX 1120", "AVM 60"]),
    st.text(min_size=1, max_size=50).filter(
        lambda s: s and not any(x in s for x in ["40", "70", "90", "MDX", "MDA", "8", "16"])
    ),
    # x40 series models - should return 2 zones
    st.sampled_from(["MRX 540", "MRX 740", "MRX 1140", "AVM 70", "AVM 90"]),
    st.text(min_size=1, max_size=50).filter(lambda s: any(x in s for x in ["40", "70", "90"])),
    # MDX-16 models - should return 8 zones
    st.sampled_from(["MDX-16", "MDA-16"]),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDX" in s and "16" in s),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDA" in s and "16" in s),
    # MDX-8 models - should return 4 zones
    st.sampled_from(["MDX-8", "MDA-8"]),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDX" in s and "8" in s),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDA" in s and "8" in s),
))
def test_zone_count_configuration(model_name):
    """Feature: anthemav-refactoring, Property 8: Zone Count Configuration.
    
    For any model implementation, when queried for zone count with a valid model name,
    the returned zone count should match the model's specification (2 for x20/x40,
    4 for MDX-8, 8 for MDX-16).
    
    Validates: Requirements 9.1, 9.7
    """
    # Create registry and get the appropriate model
    registry = ModelRegistry()
    detected_model = registry.detect_model(model_name)
    
    # Verify a model was detected
    assert detected_model is not None, \
        f"No model detected for '{model_name}'"
    
    # Get the zone count from the model
    zone_count = detected_model.get_zone_count(model_name)
    
    # Verify zone count is valid (at least 1)
    assert zone_count >= 1, \
        f"Invalid zone count {zone_count} for model '{model_name}'"
    
    # Determine expected zone count based on model name
    model_series = detected_model.get_model_series()
    
    if model_series == "x20":
        expected_zone_count = 2
    elif model_series == "x40":
        expected_zone_count = 2
    elif model_series == "mdx":
        # MDX zone count depends on specific model
        if "16" in model_name:
            expected_zone_count = 8
        elif "8" in model_name:
            expected_zone_count = 4
        else:
            expected_zone_count = 1  # Default for unknown MDX models
    else:
        # Unknown series, accept any valid zone count
        expected_zone_count = zone_count
    
    assert zone_count == expected_zone_count, \
        f"Zone count mismatch for '{model_name}': expected {expected_zone_count}, " \
        f"got {zone_count}"


@settings(max_examples=100)
@given(model_name=st.one_of(
    # x20 series models - should return empty list (all inputs available)
    st.sampled_from(["MRX 520", "MRX 720", "MRX 1120", "AVM 60"]),
    st.text(min_size=1, max_size=50).filter(
        lambda s: s and not any(x in s for x in ["40", "70", "90", "MDX", "MDA", "8", "16"])
    ),
    # x40 series models - should return empty list (all inputs available)
    st.sampled_from(["MRX 540", "MRX 740", "MRX 1140", "AVM 70", "AVM 90"]),
    st.text(min_size=1, max_size=50).filter(lambda s: any(x in s for x in ["40", "70", "90"])),
    # MDX-16 models - should return empty list (all inputs available)
    st.sampled_from(["MDX-16", "MDA-16"]),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDX" in s and "16" in s),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDA" in s and "16" in s),
    # MDX-8 models - should return [1, 2, 3, 4, 9] (limited inputs)
    st.sampled_from(["MDX-8", "MDA-8"]),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDX" in s and "8" in s),
    st.text(min_size=1, max_size=50).filter(lambda s: "MDA" in s and "8" in s),
))
def test_input_number_configuration(model_name):
    """Feature: anthemav-refactoring, Property 9: Input Number Configuration.
    
    For any model implementation, when queried for available input numbers with a
    valid model name, the returned list should match the model's specification
    (empty list for x20/x40/MDX-16, [1,2,3,4,9] for MDX-8).
    
    Validates: Requirements 9.6, 9.7
    """
    # Create registry and get the appropriate model
    registry = ModelRegistry()
    detected_model = registry.detect_model(model_name)
    
    # Verify a model was detected
    assert detected_model is not None, \
        f"No model detected for '{model_name}'"
    
    # Get the available input numbers from the model
    available_inputs = detected_model.get_available_input_numbers(model_name)
    
    # Verify the result is a list
    assert isinstance(available_inputs, list), \
        f"Available inputs should be a list, got {type(available_inputs)}"
    
    # Determine expected input numbers based on model
    model_series = detected_model.get_model_series()
    
    if model_series == "x20":
        expected_inputs = []  # All inputs available
    elif model_series == "x40":
        expected_inputs = []  # All inputs available
    elif model_series == "mdx":
        # MDX input availability depends on specific model
        if "8" in model_name:
            expected_inputs = [1, 2, 3, 4, 9]  # MDX-8 limited inputs
        else:
            expected_inputs = []  # MDX-16 has all inputs
    else:
        # Unknown series, accept any list
        expected_inputs = available_inputs
    
    assert available_inputs == expected_inputs, \
        f"Input number configuration mismatch for '{model_name}': " \
        f"expected {expected_inputs}, got {available_inputs}"
    
    # Verify all input numbers are valid (1-99) if list is not empty
    if available_inputs:
        for input_num in available_inputs:
            assert isinstance(input_num, int), \
                f"Input number should be int, got {type(input_num)}"
            assert 1 <= input_num <= 99, \
                f"Input number {input_num} out of valid range (1-99)"


@settings(max_examples=100)
@given(model_series=st.sampled_from(["x20", "x40", "mdx"]))
def test_command_set_configuration(model_series):
    """Feature: anthemav-refactoring, Property 10: Command Set Configuration.
    
    For any model implementation, the commands to query, commands to ignore, and
    supported command sets should be mutually exclusive and complete (no command
    should be both queried and ignored, and all model-specific commands should be
    accounted for).
    
    Validates: Requirements 10.1, 10.2, 10.3
    """
    # Get the model instance based on series
    if model_series == "x20":
        model = X20Model()
    elif model_series == "x40":
        model = X40Model()
    elif model_series == "mdx":
        model = MDXModel()
    else:
        raise ValueError(f"Unknown model series: {model_series}")
    
    # Get command sets from the model
    commands_to_query = model.get_commands_to_query()
    commands_to_ignore = model.get_commands_to_ignore()
    
    # Verify both are lists
    assert isinstance(commands_to_query, list), \
        f"Commands to query should be a list, got {type(commands_to_query)}"
    assert isinstance(commands_to_ignore, list), \
        f"Commands to ignore should be a list, got {type(commands_to_ignore)}"
    
    # Verify all commands are strings
    for cmd in commands_to_query:
        assert isinstance(cmd, str), \
            f"Command to query should be string, got {type(cmd)}"
        assert len(cmd) > 0, \
            f"Command to query should not be empty string"
    
    for cmd in commands_to_ignore:
        assert isinstance(cmd, str), \
            f"Command to ignore should be string, got {type(cmd)}"
        assert len(cmd) > 0, \
            f"Command to ignore should not be empty string"
    
    # Convert to sets for intersection check
    query_set = set(commands_to_query)
    ignore_set = set(commands_to_ignore)
    
    # Verify no duplicates within each list
    assert len(query_set) == len(commands_to_query), \
        f"Commands to query contains duplicates: {commands_to_query}"
    assert len(ignore_set) == len(commands_to_ignore), \
        f"Commands to ignore contains duplicates: {commands_to_ignore}"
    
    # Verify mutual exclusivity: no command should be both queried and ignored
    intersection = query_set & ignore_set
    assert len(intersection) == 0, \
        f"Commands appear in both query and ignore lists for {model_series}: {intersection}"
    
    # Verify model-specific command sets are properly configured
    # Each model should query its own commands and ignore other models' commands
    if model_series == "x20":
        # x20 should query x20 commands
        assert "IDN" in commands_to_query, \
            "x20 should query IDN command"
        assert "ECH" in commands_to_query, \
            "x20 should query ECH command"
        
        # x20 should ignore x40 and MDX commands
        assert "PVOL" in commands_to_ignore, \
            "x20 should ignore x40 PVOL command"
        assert "MAC" in commands_to_ignore, \
            "x20 should ignore MDX MAC command"
    
    elif model_series == "x40":
        # x40 should query x40 commands
        assert "PVOL" in commands_to_query, \
            "x40 should query PVOL command"
        assert "EMAC" in commands_to_query, \
            "x40 should query EMAC command"
        
        # x40 should ignore x20 and MDX commands
        assert "IDN" in commands_to_ignore, \
            "x40 should ignore x20 IDN command"
        assert "MAC" in commands_to_ignore, \
            "x40 should ignore MDX MAC command"
    
    elif model_series == "mdx":
        # MDX should query MDX commands
        assert "MAC" in commands_to_query, \
            "MDX should query MAC command"
        
        # MDX should ignore x20 and x40 commands
        assert "IDN" in commands_to_ignore, \
            "MDX should ignore x20 IDN command"
        assert "PVOL" in commands_to_ignore, \
            "MDX should ignore x40 PVOL command"
    
    # Verify completeness: the union of query and ignore sets should cover
    # all known model-specific commands
    all_known_commands = {
        # x20 commands
        "IDN", "ECH", "SIP", "Z1ARC", "FPB",
        # x40 commands
        "PVOL", "WMAC", "EMAC", "IS1ARC", "GCFPB", "GCTXS",
        # MDX commands
        "MAC",
    }
    
    union = query_set | ignore_set
    
    # Each model should account for all known model-specific commands
    # (either query them or ignore them)
    for cmd in all_known_commands:
        assert cmd in union, \
            f"Command '{cmd}' not accounted for in {model_series} model " \
            f"(should be in query or ignore list)"
