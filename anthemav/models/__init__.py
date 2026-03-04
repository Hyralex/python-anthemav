"""Model abstraction for Anthem AV receivers.

This package provides model-specific implementations for different Anthem
receiver series (x20, x40, MDX, etc.) and a registry pattern for model
detection and lookup.
"""

from typing import Dict, Optional
import logging

from anthemav.models.base import BaseModel
from anthemav.models.x20 import X20Model
from anthemav.models.x40 import X40Model
from anthemav.models.mdx import MDXModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for model implementations.

    The ModelRegistry provides a centralized location for registering and
    looking up model implementations. It supports model detection based on
    model identifier strings and retrieval by series identifier.
    """

    def __init__(self):
        """Initialize the model registry."""
        self._models: Dict[str, BaseModel] = {}
        self._register_default_models()

    def _register_default_models(self):
        """Register built-in model implementations."""
        self.register(X20Model())
        self.register(X40Model())
        self.register(MDXModel())

    def register(self, model: BaseModel) -> None:
        """Register a model implementation.

        Args:
            model: The model implementation to register
        """
        series = model.get_model_series()
        if series in self._models:
            logger.warning(f"Overwriting existing model registration for series: {series}")
        self._models[series] = model
        logger.debug(f"Registered model: {series}")

    def detect_model(self, model_name: str) -> Optional[BaseModel]:
        """Detect model based on model name string.

        This method analyzes the model identifier string and returns the
        appropriate model implementation. It uses pattern matching to identify
        the model series.

        Args:
            model_name: The model identifier string (e.g., 'MRX 540', 'MDX-16')

        Returns:
            Optional[BaseModel]: The detected model implementation, or None if unknown
        """
        if not model_name or model_name == "Unknown Model":
            return None

        # Check for x40 series (MRX x40, AVM 70/90)
        if any(x in model_name for x in ["40", "70", "90"]):
            return self._models.get("x40")

        # Check for MDX series
        if "MDX" in model_name or "MDA" in model_name:
            return self._models.get("mdx")

        # Default to x20 series (MRX x20, AVM 60)
        return self._models.get("x20")

    def get_model(self, series: str) -> Optional[BaseModel]:
        """Get model by series identifier.

        Args:
            series: The model series identifier (e.g., 'x20', 'x40', 'mdx')

        Returns:
            Optional[BaseModel]: The model implementation, or None if not found
        """
        return self._models.get(series)


# Global registry instance
_model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Get the global model registry.

    Returns:
        ModelRegistry: The global model registry instance
    """
    return _model_registry


__all__ = ['BaseModel', 'ModelRegistry', 'get_model_registry', 'X20Model', 'X40Model', 'MDXModel']
