"""Unit tests for model-specific command lists and behavior."""

import pytest
from anthemav import AVR
from anthemav.models import detect_model, get_model_registry
from anthemav.models.x20 import X20Model, ALM_NUMBER_X20, ALM_RESTRICTED, ALM_RESTRICTED_MODEL
from anthemav.models.x40 import X40Model, ALM_NUMBER_X40
from anthemav.models.mdx import MDXModel, ALM_NUMBER_MDX


class TestModelRegistry:
    """Test model detection and registry."""

    def test_registry_contains_all_models(self):
        """Ensure all model series are registered."""
        registry = get_model_registry()
        assert registry.get_model("x20") is not None
        assert registry.get_model("x40") is not None
        assert registry.get_model("mdx") is not None

    @pytest.mark.parametrize(
        "model_name,expected_series",
        [
            ("MRX 520", "x20"),
            ("MRX 720", "x20"),
            ("MRX 1120", "x20"),
            ("MRX 540", "x40"),
            ("MRX 740", "x40"),
            ("MRX 1140", "x40"),
            ("MRX 1190", "x40"),
            ("MDX-8", "mdx"),
            ("MDX-16", "mdx"),
            ("MDX8", "mdx"),
            ("MDX16", "mdx"),
            ("MDA8", "mdx"),
            ("MDA16", "mdx"),
        ],
    )
    def test_detect_model_series(self, model_name: str, expected_series: str):
        """Test model detection returns correct series for various model names."""
        model = detect_model(model_name)
        assert model is not None
        assert model.model_series == expected_series

    def test_detect_model_unknown(self):
        """Test unknown model returns None."""
        model = detect_model("Unknown Model")
        assert model is None

    def test_detect_model_empty(self):
        """Test empty model string returns None."""
        model = detect_model("")
        assert model is None


class TestX20Model:
    """Test x20 series model (MRX 520, 720, 1120)."""

    @pytest.fixture
    def model(self):
        return X20Model()

    def test_model_series(self, model):
        assert model.model_series == "x20"

    def test_zone_count(self, model):
        assert model.get_zone_count("MRX 520") == 2

    def test_commands_to_query(self, model):
        """x20 should query ECH and IDN."""
        assert set(model.commands_to_query) == {"ECH", "IDN"}

    def test_commands_to_ignore(self, model):
        """x20 should ignore PVOL, WMAC, EMAC, IS1ARC, GCFPB, GCTXS, MAC."""
        ignored = set(model.commands_to_ignore)
        assert "PVOL" in ignored
        assert "WMAC" in ignored
        assert "EMAC" in ignored
        assert "IS1ARC" in ignored
        assert "GCFPB" in ignored
        assert "GCTXS" in ignored
        assert "MAC" in ignored

    def test_alm_number_mapping(self, model):
        """x20 should have 15 audio listening modes."""
        assert len(model.alm_number_mapping) == 15
        assert model.alm_number_mapping == ALM_NUMBER_X20

    def test_alm_restricted(self, model):
        """x20 has restricted ALM values."""
        assert model.alm_restricted == ALM_RESTRICTED
        assert len(model.alm_restricted) == 8

    def test_alm_restricted_models(self, model):
        """x20 has restricted ALM models list."""
        assert model.alm_restricted_models == ALM_RESTRICTED_MODEL
        assert "MRX 520" in model.alm_restricted_models

    def test_available_input_numbers(self, model):
        """x20 returns empty list for available input numbers."""
        assert model.get_available_input_numbers("MRX 520") == []


class TestX40Model:
    """Test x40 series model (MRX 540, 740, 1140, 1190)."""

    @pytest.fixture
    def model(self):
        return X40Model()

    def test_model_series(self, model):
        assert model.model_series == "x40"

    def test_zone_count(self, model):
        assert model.get_zone_count("MRX 540") == 2

    def test_commands_to_query(self, model):
        """x40 should query GCTXS, EMAC, WMAC."""
        assert set(model.commands_to_query) == {"GCTXS", "EMAC", "WMAC"}

    def test_commands_to_ignore(self, model):
        """x40 should ignore IDN, ECH, SIP, Z1ARC, FPB, MAC."""
        ignored = set(model.commands_to_ignore)
        assert "IDN" in ignored
        assert "ECH" in ignored
        assert "SIP" in ignored
        assert "Z1ARC" in ignored
        assert "FPB" in ignored
        assert "MAC" in ignored

    def test_alm_number_mapping(self, model):
        """x40 should have 9 audio listening modes."""
        assert len(model.alm_number_mapping) == 9
        assert model.alm_number_mapping == ALM_NUMBER_X40

    def test_alm_restricted_empty(self, model):
        """x40 has no restricted ALM values."""
        assert model.alm_restricted == []

    def test_available_input_numbers(self, model):
        """x40 returns empty list for available input numbers."""
        assert model.get_available_input_numbers("MRX 540") == []


class TestMDXModel:
    """Test MDX series model (MDX-8, MDX-16, MDA8, MDA16)."""

    @pytest.fixture
    def model(self):
        return MDXModel()

    def test_model_series(self, model):
        assert model.model_series == "mdx"

    def test_zone_count_mdx8(self, model):
        assert model.get_zone_count("MDX-8") == 4

    def test_zone_count_mdx16(self, model):
        assert model.get_zone_count("MDX-16") == 8

    def test_zone_count_mda8(self, model):
        assert model.get_zone_count("MDA8") == 4

    def test_zone_count_mda16(self, model):
        assert model.get_zone_count("MDA16") == 8

    def test_commands_to_query(self, model):
        """MDX should only query MAC."""
        assert model.commands_to_query == ["MAC"]

    def test_commands_to_ignore(self, model):
        """MDX should ignore many zone-specific commands."""
        ignored = set(model.commands_to_ignore)
        assert "IDR" in ignored
        assert "ICN" in ignored
        assert "Z1AIC" in ignored
        assert "Z1AIN" in ignored
        assert "Z1AIR" in ignored
        assert "Z1ALM" in ignored
        assert "Z1BRT" in ignored
        assert "Z1DIA" in ignored
        assert "Z1DYN" in ignored
        assert "Z1IRH" in ignored
        assert "Z1IRV" in ignored
        assert "Z1VIR" in ignored

    def test_alm_number_mapping(self, model):
        """MDX should only have 'None' audio listening mode."""
        assert len(model.alm_number_mapping) == 1
        assert model.alm_number_mapping == ALM_NUMBER_MDX
        assert model.alm_number_mapping["None"] == 0

    def test_available_input_numbers_mdx8(self, model):
        """MDX-8 has specific available input numbers."""
        inputs = model.get_available_input_numbers("MDX-8")
        assert inputs == [1, 2, 3, 4, 9]

    def test_available_input_numbers_mdx16(self, model):
        """MDX-16 returns empty list for available input numbers."""
        assert model.get_available_input_numbers("MDX-16") == []


class TestAVRModelIntegration:
    """Test AVR class integration with model detection."""

    @pytest.mark.asyncio
    async def test_avr_sets_x20_commands(self):
        """Test AVR correctly sets ignored commands for x20 model."""
        avr = AVR()
        avr.set_model_command("MRX 520")
        
        # Should ignore x40 commands
        assert "PVOL" in avr._ignored_commands
        assert "WMAC" in avr._ignored_commands
        assert "EMAC" in avr._ignored_commands
        assert "GCTXS" in avr._ignored_commands
        
        # Should ignore MDX commands
        assert "Z1ALM" in avr._ignored_commands
        assert "Z1AIC" in avr._ignored_commands
        
        # Should NOT ignore x20 commands
        assert "IDN" not in avr._ignored_commands
        assert "ECH" not in avr._ignored_commands

    @pytest.mark.asyncio
    async def test_avr_sets_x40_commands(self):
        """Test AVR correctly sets ignored commands for x40 model."""
        avr = AVR()
        avr.set_model_command("MRX 540")
        
        # Should ignore x20 commands
        assert "IDN" in avr._ignored_commands
        assert "ECH" in avr._ignored_commands
        assert "SIP" in avr._ignored_commands
        assert "Z1ARC" in avr._ignored_commands
        
        # Should ignore MDX commands
        assert "Z1ALM" in avr._ignored_commands
        assert "Z1AIC" in avr._ignored_commands
        
        # Should NOT ignore x40 commands
        assert "PVOL" not in avr._ignored_commands
        assert "WMAC" not in avr._ignored_commands
        assert "GCTXS" not in avr._ignored_commands

    @pytest.mark.asyncio
    async def test_avr_sets_mdx_commands(self):
        """Test AVR correctly sets ignored commands for MDX model."""
        avr = AVR()
        avr.set_model_command("MDX-8")
        
        # MDX should ignore its own zone-specific commands
        assert "Z1ALM" in avr._ignored_commands
        assert "Z1AIC" in avr._ignored_commands
        assert "Z1VIR" in avr._ignored_commands
        
        # Should NOT ignore MAC (MDX query command)
        assert "MAC" not in avr._ignored_commands
        
        # MDX doesn't ignore x20/x40 commands (only non-MDX models ignore MDX commands)
        # This is intentional - MDX models can still receive x20/x40 style commands

    @pytest.mark.asyncio
    async def test_avr_alm_mapping_x20(self):
        """Test AVR uses correct ALM mapping for x20."""
        avr = AVR()
        avr.set_model_command("MRX 520")
        
        assert avr._alm_number == ALM_NUMBER_X20
        assert len(avr._alm_number) == 15

    @pytest.mark.asyncio
    async def test_avr_alm_mapping_x40(self):
        """Test AVR uses correct ALM mapping for x40."""
        avr = AVR()
        avr.set_model_command("MRX 540")
        
        assert avr._alm_number == ALM_NUMBER_X40
        assert len(avr._alm_number) == 9

    @pytest.mark.asyncio
    async def test_avr_alm_mapping_mdx(self):
        """Test AVR uses correct ALM mapping for MDX."""
        avr = AVR()
        avr.set_model_command("MDX-8")
        
        assert avr._alm_number == ALM_NUMBER_MDX
        assert len(avr._alm_number) == 1

    @pytest.mark.asyncio
    async def test_avr_available_inputs_mdx8(self):
        """Test AVR sets available input numbers for MDX-8."""
        avr = AVR()
        avr.set_model_command("MDX-8")
        
        assert avr._available_input_numbers == [1, 2, 3, 4, 9]

    @pytest.mark.asyncio
    async def test_avr_available_inputs_mdx16(self):
        """Test AVR has empty available input numbers for MDX-16."""
        avr = AVR()
        avr.set_model_command("MDX-16")
        
        assert avr._available_input_numbers == []

    @pytest.mark.asyncio
    async def test_avr_available_inputs_x20(self):
        """Test AVR has empty available input numbers for x20."""
        avr = AVR()
        avr.set_model_command("MRX 520")
        
        assert avr._available_input_numbers == []


class TestCommandListConsistency:
    """Test that command lists don't have overlapping queries/ignores."""

    def test_x20_no_overlap(self):
        """x20 commands_to_query should not be in commands_to_ignore."""
        model = X20Model()
        query_set = set(model.commands_to_query)
        ignore_set = set(model.commands_to_ignore)
        overlap = query_set & ignore_set
        assert len(overlap) == 0, f"x20 has overlapping commands: {overlap}"

    def test_x40_no_overlap(self):
        """x40 commands_to_query should not be in commands_to_ignore."""
        model = X40Model()
        query_set = set(model.commands_to_query)
        ignore_set = set(model.commands_to_ignore)
        overlap = query_set & ignore_set
        assert len(overlap) == 0, f"x40 has overlapping commands: {overlap}"

    def test_mdx_no_overlap(self):
        """MDX commands_to_query should not be in commands_to_ignore."""
        model = MDXModel()
        query_set = set(model.commands_to_query)
        ignore_set = set(model.commands_to_ignore)
        overlap = query_set & ignore_set
        assert len(overlap) == 0, f"MDX has overlapping commands: {overlap}"

    def test_all_models_have_unique_commands(self):
        """Each model series should have distinct command lists."""
        x20 = X20Model()
        x40 = X40Model()
        mdx = MDXModel()
        
        # x20 and x40 should have different query commands
        assert set(x20.commands_to_query) != set(x40.commands_to_query)
        
        # MDX should have different query commands from both
        assert set(mdx.commands_to_query) != set(x20.commands_to_query)
        assert set(mdx.commands_to_query) != set(x40.commands_to_query)
