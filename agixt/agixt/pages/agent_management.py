from __future__ import annotations
from agixtsdk import AGiXTSDK
from dataclasses import KW_ONLY, field
import rio

from typing import *  # type: ignore

base_uri = "http://localhost:7437"
api_key = "your_agixt_api_key"

ApiClient = AGiXTSDK(base_uri=base_uri, api_key=api_key)

class AgentManagement(rio.Component):
    """
    Agent Management
    """

    def build(self) -> rio.Component:
        providers = ApiClient.get_providers()
        selected_provider = (providers[0] if providers else "Select a provider")

        def handle_provider_change(value):
            selected_provider.set(value)

        return rio.Column(
            rio.Markdown(
                """
# Agent Management
""",
                width=60,
                margin_bottom=4,
                align_x=0.5,
                align_y=0,
            ),
            rio.Dropdown(
                label="Select a provider",
                options=[{"label": provider, "value": provider} for provider in providers],
                selected_value=selected_provider,  # Use 'selected_value' instead of 'value'
                on_change=handle_provider_change,
            ),
            spacing=2,
            width=60,
            margin_bottom=4,
            align_x=0.5,
            align_y=0,
        )
