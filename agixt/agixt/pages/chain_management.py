from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps

class ChainManagement(rio.Component):
    """
    Chain Management
    """

    def build(self) -> rio.Component:
        return rio.Markdown(
            """
# Chain Management


            """,
            width=60,
            margin_bottom=4,
            align_x=0.5,
            align_y=0,
        )

