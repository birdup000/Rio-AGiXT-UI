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
        agents = ApiClient.get_agents()
        selected_agent = agents[0]["name"] if agents else "Select an agent"
        providers = ApiClient.get_providers()
        selected_provider = providers[0] if providers else "Select a provider"
        extensions = ApiClient.get_extensions()

        def handle_agent_change(value):
            nonlocal selected_agent
            selected_agent = value

        def handle_provider_change(value):
            nonlocal selected_provider
            selected_provider = value

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
            rio.Column(
                rio.Text("Agents"),
                rio.Dropdown(
                    label="Select an agent",
                    options=[agent["name"] for agent in agents],
                    selected_value=selected_agent,
                    on_change=handle_agent_change,
                ),
                spacing=1,
                width=60,
                margin_bottom=4,
                align_x=0.5,
                align_y=0,
            ),
            rio.Text("Providers"),
            rio.Dropdown(
                label="Select a provider",
                options=[provider for provider in providers],
                selected_value=selected_provider,
                on_change=handle_provider_change,
            ),
            rio.Column(
                rio.Text("Extensions"),
                *[
                    rio.Row(
                        rio.Text(extension["extension_name"]),
                        rio.Switch(is_on=True)
                    )
                    for extension in extensions
                ],
                spacing=1,
                width=60,
                margin_bottom=4,
                align_x=0.5,
                align_y=0,
            ),
            spacing=2,
            width=60,
            margin_bottom=4,
            align_x=0.5,
            align_y=0,
        )
