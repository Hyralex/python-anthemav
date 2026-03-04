"""Base model interface for Anthem AV receivers."""

from abc import ABC, abstractmethod
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from anthemav.protocol import AVR


class BaseModel(ABC):
    """Base interface for all Anthem receiver models.

    This abstract class defines the contract that all model implementations
    must follow. Each model encapsulates model-specific behavior including
    command sets, zone configuration, and protocol formatting.
    """

    @abstractmethod
    def get_model_series(self) -> str:
        """Return the model series identifier.

        Returns:
            str: Model series identifier (e.g., 'x20', 'x40', 'mdx')
        """
        pass

    @abstractmethod
    def get_zone_count(self, model_name: str) -> int:
        """Return the number of zones supported by this model.

        Args:
            model_name: The specific model name (e.g., 'MRX 520', 'MDX-8')

        Returns:
            int: Number of zones supported
        """
        pass

    @abstractmethod
    def get_available_input_numbers(self, model_name: str) -> List[int]:
        """Return list of available input numbers.

        Args:
            model_name: The specific model name

        Returns:
            List[int]: List of available input numbers, or empty list for all inputs
        """
        pass

    @abstractmethod
    def get_commands_to_query(self) -> List[str]:
        """Return list of commands to query during initialization.

        Returns:
            List[str]: Commands to query on device initialization
        """
        pass

    @abstractmethod
    def get_commands_to_ignore(self) -> List[str]:
        """Return list of commands to ignore for this model.

        Returns:
            List[str]: Commands that should not be sent to this model
        """
        pass

    @abstractmethod
    def get_alm_number_mapping(self) -> Dict[str, int]:
        """Return audio listening mode name to number mapping.

        Returns:
            Dict[str, int]: Mapping of listening mode names to numbers
        """
        pass

    @abstractmethod
    def get_alm_restricted_models(self) -> List[str]:
        """Return list of model names with restricted listening modes.

        Returns:
            List[str]: Model names that have restricted ALM support
        """
        pass

    @abstractmethod
    def supports_audio_listening_mode(self) -> bool:
        """Return True if model supports audio listening modes.

        Returns:
            bool: True if audio listening modes are supported
        """
        pass

    @abstractmethod
    def supports_arc(self) -> bool:
        """Return True if model supports Anthem Room Correction.

        Returns:
            bool: True if ARC is supported
        """
        pass

    @abstractmethod
    def supports_profile(self) -> bool:
        """Return True if model supports sound profiles.

        Returns:
            bool: True if sound profiles are supported
        """
        pass

    @abstractmethod
    def get_mac_address_command(self) -> str:
        """Return the command to query MAC address.

        Returns:
            str: MAC address query command (IDN, EMAC, WMAC, or MAC)
        """
        pass

    @abstractmethod
    def get_volume_command_format(self, zone: int) -> str:
        """Return volume command format for the specified zone.

        Args:
            zone: Zone number

        Returns:
            str: Volume command format ('VOL' for attenuation or 'PVOL' for percentage)
        """
        pass

    @abstractmethod
    def format_input_query(self, input_number: int) -> str:
        """Format input name query command for this model.

        Args:
            input_number: Input number to query

        Returns:
            str: Formatted input query command
        """
        pass

    @abstractmethod
    def format_arc_command(self, zone: int, input_number: int) -> str:
        """Format ARC query/set command for this model.

        Args:
            zone: Zone number
            input_number: Input number

        Returns:
            str: Formatted ARC command
        """
        pass

    @abstractmethod
    def on_model_detected(self, avr: 'AVR') -> None:
        """Called when model is detected, allows model-specific initialization.

        Args:
            avr: The AVR instance to initialize
        """
        pass

    @abstractmethod
    def parse_message(self, message: str):
        """Parse a message in this model's format.

        Args:
            message: Raw message string from the receiver

        Returns:
            ParsedMessage object if successful, None if message cannot be parsed
        """
        pass

    @abstractmethod
    def format_message(self, parsed) -> str:
        """Format a parsed message back to string (pretty printer).

        Args:
            parsed: ParsedMessage object to format

        Returns:
            str: Formatted message string, or empty string if format not supported
        """
        pass
