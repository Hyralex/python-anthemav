"""X20 Model implementation for MRX x20 and AVM 60 series."""
from typing import Dict, List

from anthemav.models.base import BaseModel

__all__ = ["X20Model"]


class X20Model(BaseModel):
    """Model implementation for MRX x20 and AVM 60 series."""

    ALM_NUMBER = {
        "None": 0,
        "AnthemLogic Cinema": 1,
        "AnthemLogic Music": 2,
        "PLII Movie": 3,
        "PLII Music": 4,
        "Neo Cinema": 5,
        "Neo Music": 6,
        "All Channel": 7,
        "All Channel Mono": 8,
        "Mono": 9,
        "Mono-Academy": 10,
        "Mono (L)": 11,
        "Mono (R)": 12,
        "High Blend": 13,
        "Dolby Surround": 14,
    }

    COMMANDS = ["IDN", "ECH", "SIP", "Z1ARC", "FPB"]

    def get_model_series(self) -> str:
        """Return the model series identifier."""
        return "x20"

    def get_zone_count(self, model_name: str) -> int:
        """Return the number of zones supported by this model."""
        return 2

    def get_available_input_numbers(self, model_name: str) -> List[int]:
        """Return list of available input numbers, or empty list for all."""
        return []  # All inputs available

    def get_commands_to_query(self) -> List[str]:
        """Return list of commands to query during initialization."""
        return self.COMMANDS

    def get_commands_to_ignore(self) -> List[str]:
        """Return list of commands to ignore for this model."""
        # Ignore x40 and MDX commands
        return ["PVOL", "WMAC", "EMAC", "IS1ARC", "GCFPB", "GCTXS", "MAC"]

    def get_alm_number_mapping(self) -> Dict[str, int]:
        """Return audio listening mode name to number mapping."""
        return self.ALM_NUMBER

    def get_alm_restricted_models(self) -> List[str]:
        """Return list of model names with restricted listening modes."""
        return ["MRX 520"]

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
        """Return volume command format ('VOL' for attenuation or 'PVOL' for percentage)."""
        return "VOL"  # Attenuation format

    def format_input_query(self, input_number: int) -> str:
        """Format input name query command for this model."""
        return f"ISN{input_number:02d}"

    def format_arc_command(self, zone: int, input_number: int) -> str:
        """Format ARC query/set command for this model."""
        return f"Z{zone}ARC"

    def on_model_detected(self, avr: 'AVR') -> None:
        """Called when model is detected, allows model-specific initialization."""
        avr.command("ECH1")  # Enable TX status
        avr.query("IDN")     # Query MAC address

    def parse_message(self, message: str):
        """Parse a message in x20 format (ISNxx).

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
            parsed_message.zone = 0  # x20 format doesn't encode zone in message
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
