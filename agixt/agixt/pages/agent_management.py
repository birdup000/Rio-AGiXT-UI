from __future__ import annotations
from agixtsdk import AGiXTSDK
import rio
from typing import *
import asyncio

# Initialize API Client
base_uri = "http://localhost:7437"
api_key = "your_agixt_api_key"
ApiClient = AGiXTSDK(base_uri=base_uri, api_key=api_key)

# You can define your own functions for these based on your requirements.
def prompt_selection(prompt, show_user_input):
    return {}

def chain_selection(prompt, show_user_input):
    return {}

def command_selection(prompt, show_user_input):
    return {}



class MultiSelect(rio.Component):
    options: List[Dict[str, Any]]
    selected: Set[str] = set()
    settings: Dict[str, Dict[str, str]] = {}

    _is_open: bool = False

    async def _toggle_open(self) -> None:
        self._is_open = not self._is_open
        await self.force_refresh()  # Force refresh to update the popup state

    async def _toggle_selection(self, option: Dict[str, Any]) -> None:
        extension_name = option["name"]
        if extension_name in self.selected:
            self.selected.remove(extension_name)
            self.settings.pop(extension_name, None)
        else:
            self.selected.add(extension_name)
            self.settings[extension_name] = {setting: "" for setting in option["settings"]}
        await self.force_refresh()  # Force refresh to update the popup state

    def _update_setting(self, extension_name: str, setting: str, value: str) -> None:
        if extension_name in self.settings:
            self.settings[extension_name][setting] = value

    def build(self) -> rio.Component:
        grid = rio.Grid(row_spacing=0.4, column_spacing=0.5)  # Increased spacing for better readability

        row_index = 0

        for option in self.options:
            grid.add(
                rio.Text(
                    option["display"],
                    justify='left',
                    style=rio.TextStyle(
                        font_weight='bold',
                        fill=rio.Color.from_hex("#333")
                    )
                ),  # Text styling
                row=row_index, column=0
            )
            grid.add(
                rio.Switch(
                    is_on=option["name"] in self.selected,
                    on_change=lambda _, opt=option: asyncio.create_task(self._toggle_selection(opt)),
                ),
                row=row_index, column=1
            )
            status_text = "🌟 Enabled" if option["name"] in self.selected else "🔒 Disabled"  # Emoji for better visualization
            grid.add(
                rio.Text(
                    status_text,
                    style=rio.TextStyle(
                        italic=True,
                        fill=rio.Color.from_hex("#666")
                    )
                ),  # Text styling
                row=row_index, column=2
            )

            row_index += 1

            if option["name"] in self.selected:
                for setting in option["settings"]:
                    grid.add(
                        rio.Text(
                            f"⚙️ {setting}",
                            style=rio.TextStyle(
                                fill=rio.Color.from_hex("#007bff")
                            )
                        ),  # Styled settings text
                        row=row_index, column=0
                    )
                    grid.add(
                        rio.TextInput(
                            text=self.settings.get(option["name"], {}).get(setting, ""),
                            on_change=lambda value, ext_name=option["name"], setting=setting: self._update_setting(ext_name, setting, value),
                        ),
                        row=row_index, column=1, width=2
                    )
                    row_index += 1

        done_button = rio.Button(
            "🛑 Done",
            on_press=lambda: asyncio.create_task(self._toggle_open()),
            style='major',  # Use predefined style
        )
        grid.add(done_button, row=row_index, column=0, width=3)

        return rio.Popup(
            anchor=rio.Button(
                "🛠 Edit Selection",
                on_press=lambda: asyncio.create_task(self._toggle_open()),
                style='major',  # Use predefined style
            ),
            content=rio.ScrollContainer(
                content=grid,
                scroll_y='always',
                scroll_x='never',
                height=40,  # Increased height for more content visibility
                width=100,  # Adjusted width for better layout
                margin=0.4,  # Increased margin for better spacing
            ),
            is_open=self._is_open,
            alignment=0.5,
            gap=0.4,  # Increased gap for better spacing
            width='grow',
            height='grow',
        )











class AgentManagement(rio.Component):
    """
    Agent Management
    """

    selected: set[str] = set()

    def render_provider_settings(self, provider_name, agent_settings, provider_settings):
        settings = ApiClient.get_provider_settings(provider_name=provider_name)
        for key, value in settings.items():
            if key in provider_settings:
                settings[key] = provider_settings[key]
            else:
                # Add an indented block here
                pass
        provider_settings.update(settings)
        return provider_settings

    def build(self) -> rio.Component:
        def log_error(message: str):
            print(f"Error: {message}")  # Simple logging function for debugging

        try:
            agents = ApiClient.get_agents()
        except Exception as e:
            log_error(f"Error fetching agents: {e}")
            agents = []

        try:
            providers = ApiClient.get_providers()
        except Exception as e:
            log_error(f"Error fetching providers: {e}")
            providers = []

        try:
            extensions = ApiClient.get_extension_settings()
        except Exception as e:
            log_error(f"Error fetching extensions: {e}")
            extensions = {}

        agent_action = rio.Dropdown(
            label="Action",
            options=["Create Agent", "Modify Agent", "Delete Agent"],
            selected_value="Create Agent",
        )

        if agent_action.selected_value == "Create Agent":
            agent_name = rio.TextInput("", label="Enter the agent name:")
        else:
            agent_names = [agent.get("name", "Unnamed agent") for agent in agents]
            agent_name = rio.Dropdown(
                label="Select an agent:",
                options=agent_names,
                selected_value=agent_names[0] if agent_names else "",
            )

        agent_config = {}
        agent_settings = {}
        agent_commands = {}

        if agent_action.selected_value == "Modify Agent":
            agent_config = ApiClient.get_agentconfig(agent_name.value)
            agent_settings = agent_config.get("settings", {})
            agent_commands = agent_config.get("commands", {})

        provider_settings = {}

        language_providers = ApiClient.get_providers_by_service("llm")
        selected_language_provider = rio.Dropdown(
            label="Select language provider:",
            options=language_providers if language_providers else ["No providers"],
            selected_value=agent_settings.get("provider", language_providers[0] if language_providers else ""),
        )
        provider_settings = self.render_provider_settings(selected_language_provider.selected_value, agent_settings, provider_settings)

        vision_providers = ["None"] + (ApiClient.get_providers_by_service("vision") or [])
        selected_vision_provider = rio.Dropdown(
            label="Select vision provider:",
            options=vision_providers,
            selected_value=agent_settings.get("vision_provider", "None"),
        )
        if selected_vision_provider.selected_value != "None":
            provider_settings = self.render_provider_settings(selected_vision_provider.selected_value, agent_settings, provider_settings)

        tts_providers = ["None"] + (ApiClient.get_providers_by_service("tts") or [])
        selected_tts_provider = rio.Dropdown(
            label="Select text to speech provider:",
            options=tts_providers,
            selected_value=agent_settings.get("tts_provider", "None"),
        )
        provider_settings = self.render_provider_settings(selected_tts_provider.selected_value, agent_settings, provider_settings)

        stt_providers = ApiClient.get_providers_by_service("transcription") or []
        selected_stt_provider = rio.Dropdown(
            label="Select speech to text provider:",
            options=stt_providers,
            selected_value=agent_settings.get("transcription_provider", stt_providers[0] if stt_providers else ""),
        )
        provider_settings = self.render_provider_settings(selected_stt_provider.selected_value, agent_settings, provider_settings)

        image_providers = ["None"] + (ApiClient.get_providers_by_service("image") or [])
        selected_img_provider = agent_settings.get("image_provider", "None")
        selected_image_provider = rio.Dropdown(
            label="Select image generation provider:",
            options=image_providers,
            selected_value=selected_img_provider,
        )
        if selected_image_provider.selected_value != "None":
            provider_settings = self.render_provider_settings(selected_image_provider.selected_value, agent_settings, provider_settings)

        embedding_providers = ApiClient.get_providers_by_service("embeddings") or []
        selected_embedding_provider = rio.Dropdown(
            label="Select embeddings provider:",
            options=embedding_providers,
            selected_value=agent_settings.get("embeddings_provider", embedding_providers[0] if embedding_providers else ""),
        )

        extension_options = [
            {
                "name": key,  # use the keys of the extensions dictionary as names
                "display": f'{key} ({", ".join(value.keys())})' if value else f'{key} ()',
                "settings": value
            }
            for key, value in extensions.items()
        ]

        multi_select_extension = MultiSelect(
            options=extension_options,
        )

        helper_agent = rio.Dropdown(
            label="Select helper agent (Optional):",
            options=["None"] + [agent.get("name", "Unnamed agent") for agent in agents],
            selected_value=agent_settings.get("helper_agent_name", "None"),
        )

        chat_completions_mode = rio.Dropdown(
            label="Select chat completions mode:",
            options=[("Prompt", "prompt"), ("Chain", "chain"), ("Command", "command")],
            selected_value=agent_settings.get("mode", "prompt"),
        )

        prompt_settings_elements = []
        chain_settings_elements = []
        command_settings_elements = []
        command_variable = None

        if chat_completions_mode.selected_value == "prompt":
            prompt_settings = prompt_selection(prompt=agent_settings, show_user_input=False)
            prompt_settings_elements = [rio.TextInput(label=key, default=str(prompt_settings[key])) for key in prompt_settings]

        if chat_completions_mode.selected_value == "chain":
            chain_settings = chain_selection(prompt=agent_settings, show_user_input=False)
            chain_settings_elements = [rio.TextInput(label=key, default=str(chain_settings[key])) for key in chain_settings]

        if chat_completions_mode.selected_value == "command":
            command_settings = command_selection(prompt=agent_settings, show_user_input=False)
            command_settings_elements = [rio.TextInput(label=key, default=str(command_settings[key])) for key in command_settings]
            if command_settings and "command_args" in command_settings:
                command_variable = rio.Dropdown(
                    label="Select Command Variable",
                    options=[""] + list(command_settings["command_args"].keys()),
                    selected_value=agent_settings.get("command_variable", ""),
                )

        def save_agent_settings():
            settings = {
                "provider": selected_language_provider.selected_value,
                **{key: value.text if isinstance(value, rio.TextInput) else value.selected_value for key, value in provider_settings.items() if isinstance(value, rio.Component)},
                "vision_provider": selected_vision_provider.selected_value,
                "transcription_provider": selected_stt_provider.selected_value,
                "translation_provider": selected_stt_provider.selected_value,
                "tts_provider": selected_tts_provider.selected_value if selected_tts_provider.selected_value != "None" else "None",
                "image_provider": selected_image_provider.selected_value if selected_image_provider.selected_value != "None" else "None",
                "embeddings_provider": selected_embedding_provider.selected_value,
                "helper_agent_name": helper_agent.selected_value,
                **{key: value for extension, settings in multi_select_extension.settings.items() for key, value in settings.items()},
                "mode": chat_completions_mode.selected_value,
            }

            if chat_completions_mode.selected_value == "prompt":
                settings.update({key: element.text for key, element in zip(prompt_settings, prompt_settings_elements)})

            if chat_completions_mode.selected_value == "chain":
                settings.update({key: element.text for key, element in zip(chain_settings, chain_settings_elements)})

            if chat_completions_mode.selected_value == "command":
                settings.update({key: element.text for key, element in zip(command_settings, command_settings_elements)})
                settings["command_variable"] = command_variable.selected_value if command_variable else ""

            selected_commands = []  # Define the variable and assign an empty list
            commands = {command: True for command in selected_commands}

            if agent_action.selected_value == "Create Agent":
                response = ApiClient.add_agent(agent_name=agent_name.text, settings=settings, commands=commands)
                print(f"Agent '{agent_name.text}' created.")
            elif agent_action.selected_value == "Modify Agent":
                response = ApiClient.update_agent_settings(agent_name=agent_name.selected_value, settings=settings)
                response = ApiClient.update_agent_commands(agent_name=agent_name.selected_value, commands=commands)
                print(f"Agent '{agent_name.selected_value}' updated.")
            elif agent_action.selected_value == "Delete Agent":
                response = ApiClient.delete_agent(agent_name.selected_value)
                print(f"Agent '{agent_name.selected_value}' deleted.")

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
            agent_action,
            agent_name,
            rio.Markdown("## Select Providers"),
            rio.Row(
                rio.Column(
                    rio.Markdown("### Language Provider"),
                    selected_language_provider,
                    *[component for component in provider_settings.values() if isinstance(component, rio.Component)],
                ),
                rio.Column(
                    rio.Markdown("### Vision Provider (Optional)"),
                    selected_vision_provider,
                    *([component for component in provider_settings.values() if isinstance(component, rio.Component)] if selected_vision_provider.selected_value != "None" else [rio.Container(content=rio.Text(""))]),
                    rio.Markdown("### Text to Speech Provider"),
                    selected_tts_provider,
                    *[component for component in provider_settings.values() if isinstance(component, rio.Component)],
                    rio.Markdown("### Speech to Text Provider"),
                    selected_stt_provider,
                    *[component for component in provider_settings.values() if isinstance(component, rio.Component)],
                    rio.Markdown("### Image Generation Provider (Optional)"),
                    selected_image_provider,
                    *([component for component in provider_settings.values() if isinstance(component, rio.Component)] if selected_image_provider.selected_value != "None" else [rio.Container(content=rio.Text(""))]),
                    rio.Markdown("### Embeddings Provider"),
                    selected_embedding_provider,
                ),
            ),
            rio.Markdown("## Configure Chat Completions Mode"),
            chat_completions_mode,
            *prompt_settings_elements if chat_completions_mode.selected_value == "prompt" else [],
            *chain_settings_elements if chat_completions_mode.selected_value == "chain" else [],
            rio.Row(
                rio.Column(*command_settings_elements if chat_completions_mode.selected_value == "command" else []),
                rio.Column(command_variable if chat_completions_mode.selected_value == "command" else rio.Container(content=rio.Text(""))),
            ),
            rio.Markdown("## Agent Extensions"),
            multi_select_extension,
            rio.Button(
                "Save Agent Settings",
                on_press=lambda: save_agent_settings(),
            ),
        )
