"""Model implementation for Anthem x40 series receivers."""

from typing import Dict, List

from anthemav.models.base import BaseModel

ALM_NUMBER_X40 = {
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


class X40Model(BaseModel):
    """Model implementation for Anthem x40 series receivers."""

    @property
    def model_series(self) -> str:
        return "x40"

    def get_zone_count(self, model_name: str) -> int:
        return 2

    def get_available_input_numbers(self, model_name: str) -> List[int]:
        return []

    @property
    def commands_to_query(self) -> List[str]:
        return ["GCTXS", "EMAC", "WMAC"]

    @property
    def commands_to_ignore(self) -> List[str]:
        return ["IDN", "ECH", "SIP", "Z1ARC", "FPB", "MAC"]

    @property
    def alm_number_mapping(self) -> Dict[str, int]:
        return ALM_NUMBER_X40
