"""Model abstraction for Anthem AV receivers."""

from typing import Dict, Optional

from anthemav.models.base import BaseModel
from anthemav.models.x20 import X20Model
from anthemav.models.x40 import X40Model
from anthemav.models.mdx import MDXModel


class ModelRegistry:
    """Registry for model implementations."""

    def __init__(self):
        self._models: Dict[str, BaseModel] = {}
        self._register_default_models()

    def _register_default_models(self):
        self.register(X20Model())
        self.register(X40Model())
        self.register(MDXModel())

    def register(self, model: BaseModel) -> None:
        series = model.model_series
        self._models[series] = model

    def detect_model(self, model_name: str) -> Optional[BaseModel]:
        if not model_name or model_name == "Unknown Model":
            return None
        if any(x in model_name for x in ["40", "70", "90"]):
            return self._models.get("x40")
        if "MDX" in model_name or "MDA" in model_name:
            return self._models.get("mdx")
        return self._models.get("x20")

    def get_model(self, series: str) -> Optional[BaseModel]:
        return self._models.get(series)


_model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    return _model_registry


def detect_model(model_name: str) -> Optional[BaseModel]:
    return _model_registry.detect_model(model_name)


__all__ = [
    "BaseModel",
    "ModelRegistry",
    "get_model_registry",
    "detect_model",
    "X20Model",
    "X40Model",
    "MDXModel",
]
