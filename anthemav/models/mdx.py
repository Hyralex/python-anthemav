"""Model implementation for Anthem MDX series amplifiers."""

from typing import Dict, List

from anthemav.models.base import BaseModel

ALM_NUMBER_MDX = {"None": 0}

COMMANDS_MDX_IGNORE = [
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


class MDXModel(BaseModel):
    """Model implementation for Anthem MDX series amplifiers."""

    @property
    def model_series(self) -> str:
        return "mdx"

    def get_zone_count(self, model_name: str) -> int:
        if "16" in model_name:
            return 8
        elif "8" in model_name:
            return 4
        return 4

    def get_available_input_numbers(self, model_name: str) -> List[int]:
        if "8" in model_name:
            return [1, 2, 3, 4, 9]
        return []

    @property
    def commands_to_query(self) -> List[str]:
        return ["MAC"]

    @property
    def commands_to_ignore(self) -> List[str]:
        return COMMANDS_MDX_IGNORE.copy()

    @property
    def alm_number_mapping(self) -> Dict[str, int]:
        return ALM_NUMBER_MDX
