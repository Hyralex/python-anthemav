"""MDX Model implementation for MDX distribution amplifier series."""
from typing import Dict, List

from anthemav.models.base import BaseModel

__all__ = ["MDXModel"]


class MDXModel(BaseModel):
    """Model implementation for MDX distribution amplifier series."""

    COMMANDS = ["MAC"]

    COMMANDS_TO_IGNORE = [
        "IDR",
        "ICN",
        "Z1AIC",
        "Z1AIN",
        "Z1AIR",
        "Z1ALM",
        "Z1BRT",
        "Z1DIA",
        "Z1DYN",
        "Z1IRH",
        "Z1IRV",
        "Z1VIR",
    ]

    def get_model_series(self) -> str:
        """Return the model series identifier."""
        return "mdx"

    def get_zone_count(self, model_name: str) -> int:
        """Return the number of zones supported by this model."""
        if "16" in model_name:
            return 8
        elif "8" in model_name:
            return 4
        return 1

    def get_available_input_numbers(self, model_name: str) -> List[int]:
        """Return list of available input numbers, or empty list for all."""
        if "8" in model_name:
            return [1, 2, 3, 4, 9]  # MDX-8 limited inputs
        return []  # MDX-16 has all inputs

    def get_commands_to_query(self) -> List[str]:
        """Return list of commands to query during initialization."""
        return self.COMMANDS

    def get_commands_to_ignore(self) -> List[str]:
        """Return list of commands to ignore for this model."""
        # Ignore x20 and x40 commands, plus MDX-specific ignores
        return ["IDN", "ECH", "SIP", "Z1ARC", "FPB",
                "PVOL", "WMAC", "EMAC", "IS1ARC", "GCFPB", "GCTXS"] + self.COMMANDS_TO_IGNORE

    def get_alm_number_mapping(self) -> Dict[str, int]:
        """Return audio listening mode name to number mapping."""
        return {"None": 0}  # MDX doesn't support listening modes

    def get_alm_restricted_models(self) -> List[str]:
        """Return list of model names with restricted listening modes."""
        return []

    def supports_audio_listening_mode(self) -> bool:
        """Return True if model supports audio listening modes."""
        return False

    def supports_arc(self) -> bool:
        """Return True if model supports Anthem Room Correction."""
        return False

    def supports_profile(self) -> bool:
        """Return True if model supports sound profiles."""
        return False

    def get_mac_address_command(self) -> str:
        """Return the command to query MAC address."""
        return "MAC"

    def get_volume_command_format(self, zone: int) -> str:
        """Return volume command format ('VOL' for attenuation or 'PVOL' for percentage)."""
        return "VOL"  # Direct volume format

    def format_input_query(self, input_number: int) -> str:
        """Format input name query command for this model."""
        return f"ISN{input_number:02d}"

    def format_arc_command(self, zone: int, input_number: int) -> str:
        """Format ARC query/set command for this model."""
        return ""  # MDX doesn't support ARC

    def on_model_detected(self, avr: 'AVR') -> None:
        """Called when model is detected, allows model-specific initialization."""
        avr.query("MAC")
        # MDX receivers don't return input count, populate with fixed list
        avr._populate_inputs(12)

    def parse_message(self, message: str):
        """Parse a message in MDX format (ISNxx - same as x20).

        Args:
            message: Raw message string from the receiver

        Returns:
            ParsedMessage object if successful, None if message cannot be parsed
        """
        from anthemav.parser import ParsedMessage
        
        if not message or not message.startswith("ISN") or len(message) < 5:
            return None
        
        try:
            parsed_message = ParsedMessage()
            parsed_message.command = "ISN"
            
            # Parse input number from positions 3-5 (ISNxx)
            parsed_message.input_number = int(message[3:5])
            
            # Validate input_number range (1-99)
            if parsed_message.input_number < 1 or parsed_message.input_number > 99:
                return None
            
            # Extract value - everything after ISNxx
            parsed_message.value = message[5:]
            parsed_message.zone = 0  # MDX format doesn't encode zone in message
            return parsed_message
        except (ValueError, IndexError):
            # Handle parsing errors gracefully
            return None

    def format_message(self, parsed) -> str:
        """Format a parsed message back to string (pretty printer).

        Args:
            parsed: ParsedMessage object to format

        Returns:
            str: Formatted message string, or empty string if format not supported
        """
        if not parsed or parsed.command != "ISN":
            return ""
        
        return f"ISN{parsed.input_number:02d}{parsed.value}"
