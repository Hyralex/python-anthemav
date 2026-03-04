"""X40 Model implementation for MRX x40 and AVM 70/90 series."""
from typing import Dict, List

from anthemav.models.base import BaseModel

__all__ = ["X40Model"]


class X40Model(BaseModel):
    """Model implementation for MRX x40 and AVM 70/90 series."""

    ALM_NUMBER = {
        "None": 0,
        "AnthemLogic Cinema": 1,
        "AnthemLogic Music": 2,
        "Dolby Surround": 3,
        "DTS neural:X": 4,
        "DTS Virtual:X": 5,
        "All Channel Stereo": 6,
        "Mono": 7,
        "All Channel Mono": 8,
    }

    COMMANDS = ["PVOL", "WMAC", "EMAC", "IS1ARC", "GCFPB", "GCTXS"]

    def get_model_series(self) -> str:
        """Return the model series identifier."""
        return "x40"

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
        # Ignore x20 and MDX commands
        return ["IDN", "ECH", "SIP", "Z1ARC", "FPB", "MAC"]

    def get_alm_number_mapping(self) -> Dict[str, int]:
        """Return audio listening mode name to number mapping."""
        return self.ALM_NUMBER

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
        return "EMAC"  # Primary, fallback to WMAC

    def get_volume_command_format(self, zone: int) -> str:
        """Return volume command format ('VOL' for attenuation or 'PVOL' for percentage)."""
        return "PVOL"  # Percentage format

    def format_input_query(self, input_number: int) -> str:
        """Format input name query command for this model."""
        return f"IS{input_number}IN"

    def format_arc_command(self, zone: int, input_number: int) -> str:
        """Format ARC query/set command for this model."""
        return f"IS{input_number}ARC"

    def on_model_detected(self, avr: 'AVR') -> None:
        """Called when model is detected, allows model-specific initialization."""
        avr.query("GCTXS")  # Query TX status
        avr.query("EMAC")   # Query Ethernet MAC
        avr.query("WMAC")   # Query WiFi MAC

    def parse_message(self, message: str):
        """Parse a message in x40 format (ISxCOMMAND).

        Handles both ARC and IN command formats.

        Args:
            message: Raw message string from the receiver

        Returns:
            ParsedMessage object if successful, None if message cannot be parsed
        """
        from anthemav.parser import ParsedMessage
        
        if not message:
            return None
        
        # Try ARC command
        result = self._parse_x40_input_message(message, "ARC")
        if result:
            return result
        
        # Try IN command (input names)
        result = self._parse_x40_input_message(message, "IN")
        if result:
            return result
        
        return None

    def _parse_x40_input_message(self, message: str, command: str):
        """Parse x40 input-specific message.

        Args:
            message: Raw message string
            command: Command type (ARC or IN)

        Returns:
            ParsedMessage object if successful, None otherwise
        """
        from anthemav.parser import ParsedMessage
        
        if not message or not command:
            return None
        
        if (
            message.startswith("IS")
            and command in message
            and len(message) >= len(command) + 4
        ):
            try:
                parsed_message = ParsedMessage()
                command_position = message.index(command)
                parsed_message.command = message[0 : command_position + len(command)]
                
                # Parse and validate input_number
                input_number_str = message[2:command_position]
                if not input_number_str:
                    return None
                
                parsed_message.input_number = int(input_number_str)
                
                # Validate input_number range (1-99)
                if parsed_message.input_number < 1 or parsed_message.input_number > 99:
                    return None
                
                # Extract value - handles special characters in the value string
                parsed_message.value = message[command_position + len(command) :]
                parsed_message.zone = 0  # x40 format doesn't encode zone in message
                return parsed_message
            except (ValueError, IndexError, UnicodeError):
                # Handle parsing errors and encoding issues gracefully
                return None
        return None

    def format_message(self, parsed) -> str:
        """Format a parsed message back to string (pretty printer).

        Args:
            parsed: ParsedMessage object to format

        Returns:
            str: Formatted message string, or empty string if format not supported
        """
        if not parsed:
            return ""
        
        # x40 format: ISxCOMMAND where COMMAND is ARC or IN
        if parsed.command.endswith("ARC"):
            return f"IS{parsed.input_number}ARC{parsed.value}"
        elif parsed.command.endswith("IN"):
            return f"IS{parsed.input_number}IN{parsed.value}"
        
        return ""
