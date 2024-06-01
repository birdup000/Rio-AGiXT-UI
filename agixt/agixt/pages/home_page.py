from __future__ import annotations

from dataclasses import KW_ONLY, field
from typing import *  # type: ignore

import rio

from .. import components as comps

class HomePage(rio.Component):
    """
    The home page of AGiXT, featuring a logo and a brief introduction.
    """

    def build(self) -> rio.Component:
        return rio.Column(
                        rio.Html(f"""
                <img src="https://josh-xt.github.io/AGiXT/images/AGiXT-gradient-light.svg" width="200">
            """),
            rio.Text("Welcome to AGiXT", style="heading1"),
            rio.Text("Your AI-powered assistant for streamlining tasks and workflows"),
            spacing=2,
            width=60,
            margin_bottom=4,
            align_x=0.5,
            align_y=0,
        )