"""Base model interface for Anthem AV receivers."""

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseModel(ABC):
    """Base interface for all Anthem receiver models."""

    @property
    @abstractmethod
    def model_series(self) -> str:
        """Return the model series identifier."""
        pass

    @abstractmethod
    def get_zone_count(self, model_name: str) -> int:
        """Return the number of zones supported by this model."""
        pass

    @abstractmethod
    def get_available_input_numbers(self, model_name: str) -> List[int]:
        """Return list of available input numbers."""
        pass

    @property
    @abstractmethod
    def commands_to_query(self) -> List[str]:
        """Return list of commands to query during initialization."""
        pass

    @property
    @abstractmethod
    def commands_to_ignore(self) -> List[str]:
        """Return list of commands to ignore for this model."""
        pass

    @property
    @abstractmethod
    def alm_number_mapping(self) -> Dict[str, int]:
        """Return audio listening mode name to number mapping."""
        pass

    @property
    def alm_restricted_models(self) -> List[str]:
        """Return list of model names with restricted listening modes."""
        return []

    @property
    def alm_restricted(self) -> List[str]:
        """Return list of restricted listening mode values."""
        return []
