"""Model implementation for Anthem x20 series receivers."""

from typing import Dict, List

from anthemav.models.base import BaseModel

ALM_NUMBER_X20 = {
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

ALM_RESTRICTED = ["00", "01", "02", "03", "04", "05", "06", "07"]
ALM_RESTRICTED_MODEL = ["MRX 520"]


class X20Model(BaseModel):
    """Model implementation for Anthem x20 series receivers."""

    @property
    def model_series(self) -> str:
        return "x20"

    def get_zone_count(self, model_name: str) -> int:
        return 2

    def get_available_input_numbers(self, model_name: str) -> List[int]:
        return []

    @property
    def commands_to_query(self) -> List[str]:
        return ["ECH", "IDN"]

    @property
    def commands_to_ignore(self) -> List[str]:
        return ["PVOL", "WMAC", "EMAC", "IS1ARC", "GCFPB", "GCTXS", "MAC"]

    @property
    def alm_number_mapping(self) -> Dict[str, int]:
        return ALM_NUMBER_X20

    @property
    def alm_restricted(self) -> List[str]:
        return ALM_RESTRICTED

    @property
    def alm_restricted_models(self) -> List[str]:
        return ALM_RESTRICTED_MODEL
