from __future__ import annotations
from agixtsdk import AGiXTSDK
import rio
from typing import *
import asyncio

# Initialize API Client
base_uri = "http://localhost:7437"
api_key = "YOUR_API_KEY"
ApiClient = AGiXTSDK(base_uri=base_uri, api_key=api_key)


class MultiSelect(rio.Component):
    options: List[Dict[str, Any]]
    selected: Set[str] = set()
    settings: Dict[str, Dict[str, str]] = {}

    _is_open: bool = False

    async def _toggle_open(self) -> None:
        self._is_open = not self._is_open
        await self.force_refresh()

    async def _toggle_selection(self, option: Dict[str, Any]) -> None:
        extension_name = option["name"]
        if extension_name in self.selected:
            self.selected.remove(extension_name)
            self.settings.pop(extension_name, None)
        else:
            self.selected.add(extension_name)
            self.settings[extension_name] = {
                setting: "" for setting in option["settings"]
            }
        await self.force_refresh()

    def _update_setting(self, extension_name: str, setting: str, value: str) -> None:
        if extension_name in self.settings:
            self.settings[extension_name][setting] = value

    def build(self) -> rio.Component:
        grid = rio.Grid(row_spacing=0.4, column_spacing=0.5)

        row_index = 0

        for option in self.options:
            grid.add(
                rio.Text(
                    option["display"],
                    justify="left",
                    style=rio.TextStyle(
                        font_weight="bold", fill=rio.Color.from_hex("#333")
                    ),
                ),
                row=row_index,
                column=0,
            )
            grid.add(
                rio.Switch(
                    is_on=option["name"] in self.selected,
                    on_change=lambda _, opt=option: asyncio.create_task(
                        self._toggle_selection(opt)
                    ),
                ),
                row=row_index,
                column=1,
            )
            status_text = (
                "🌟 Enabled" if option["name"] in self.selected else "🔒 Disabled"
            )
            grid.add(
                rio.Text(
                    status_text,
                    style=rio.TextStyle(italic=True, fill=rio.Color.from_hex("#666")),
                ),
                row=row_index,
                column=2,
            )

            row_index += 1

            if option["name"] in self.selected:
                for setting in option["settings"]:
                    grid.add(
                        rio.Text(
                            f"⚙️ {setting}",
                            style=rio.TextStyle(fill=rio.Color.from_hex("#007bff")),
                        ),
                        row=row_index,
                        column=0,
                    )
                    grid.add(
                        rio.TextInput(
                            text=self.settings.get(option["name"], {}).get(setting, ""),
                            on_change=lambda value, ext_name=option[
                                "name"
                            ], setting=setting: self._update_setting(
                                ext_name, setting, value
                            ),
                        ),
                        row=row_index,
                        column=1,
                        width=2,
                    )
                    row_index += 1

        done_button = rio.Button(
            "🛑 Done",
            on_press=lambda: asyncio.create_task(self._toggle_open()),
            style="major",
        )
        grid.add(done_button, row=row_index, column=0, width=3)

        return rio.Popup(
            anchor=rio.Button(
                "🛠 Edit Selection",
                on_press=lambda: asyncio.create_task(self._toggle_open()),
                style="major",
            ),
            content=rio.ScrollContainer(
                content=grid,
                scroll_y="always",
                scroll_x="never",
                height=40,
                width=100,
                margin=0.4,
            ),
            is_open=self._is_open,
            alignment=0.5,
            gap=0.4,
            width="grow",
            height="grow",
        )


class AgentManagement(rio.Component):
    """
    Agent Management
    """

    selected: set[str] = set()
    message: str = ""
    is_error: bool = False

    def get_provider_settings_safe(self, provider_name):
        try:
            settings = ApiClient.get_provider_settings(provider_name=provider_name)
            return settings if isinstance(settings, dict) else {}
        except Exception as e:
            print(f"Error getting provider settings for {provider_name}: {str(e)}")
            return {}

    def render_provider_settings(
        self, provider_name, agent_settings, provider_settings
    ):
        try:
            settings = self.get_provider_settings_safe(provider_name)
            for key, value in settings.items():
                if key in provider_settings:
                    settings[key] = provider_settings[key]
                else:
                    settings[key] = rio.TextInput(
                        text=str(agent_settings.get(key, value)),
                        label=f"{key}:",
                    )
            provider_settings.update(settings)
            return provider_settings
        except Exception as e:
            print(f"Error rendering provider settings for {provider_name}: {str(e)}")
            return provider_settings

    def get_providers_safe(self):
        try:
            return ApiClient.get_providers()
        except Exception as e:
            print(f"Error getting providers: {str(e)}")
            return []  # Return an empty list if there's an error

    async def save_agent_settings(self, agent_action, agent_name, settings, commands):
        try:
            if agent_action == "Create Agent":
                response = await ApiClient.add_agent(
                    agent_name=agent_name, settings=settings, commands=commands
                )
                self.set_message(f"Agent '{agent_name}' created successfully.", False)
            elif agent_action == "Modify Agent":
                response = await ApiClient.update_agent_settings(
                    agent_name=agent_name, settings=settings
                )
                await ApiClient.update_agent_commands(
                    agent_name=agent_name, commands=commands
                )
                self.set_message(f"Agent '{agent_name}' updated successfully.", False)
            elif agent_action == "Delete Agent":
                response = await ApiClient.delete_agent(agent_name)
                self.set_message(f"Agent '{agent_name}' deleted successfully.", False)
        except Exception as e:
            self.set_message(f"Error: {str(e)}", True)

    def set_message(self, message: str, is_error: bool = False):
        self.message = message
        self.is_error = is_error

    def prompt_selection(self, prompt: dict = {}, show_user_input: bool = True):
        prompt_categories = ApiClient.get_prompt_categories()
        prompt_category = rio.Dropdown(
            label="Select Prompt Category",
            options=prompt_categories,
            selected_value=prompt_categories[0] if prompt_categories else "Default",
        )
        available_prompts = ApiClient.get_prompts(
            prompt_category=prompt_category.selected_value
        )
        prompt_name = rio.Dropdown(
            label="Select Custom Prompt",
            options=available_prompts,
            selected_value=prompt.get(
                "prompt_name", available_prompts[0] if available_prompts else ""
            ),
        )
        prompt_content = ApiClient.get_prompt(
            prompt_name=prompt_name.selected_value,
            prompt_category=prompt_category.selected_value,
        )
        prompt_args = ApiClient.get_prompt_args(
            prompt_name=prompt_name.selected_value,
            prompt_category=prompt_category.selected_value,
        )
        args = {
            arg: rio.TextInput(label=arg, text=str(prompt.get(arg, "")))
            for arg in prompt_args
            if arg != "user_input" or show_user_input
        }
        return {
            "prompt_name": prompt_name.selected_value,
            "prompt_category": prompt_category.selected_value,
            **{key: value.text for key, value in args.items()},
        }

    def chain_selection(self, prompt: dict = {}, show_user_input: bool = True):
        available_chains = ApiClient.get_chains()
        chain_name = rio.Dropdown(
            label="Select Chain",
            options=available_chains,
            selected_value=prompt.get(
                "chain", available_chains[0] if available_chains else ""
            ),
        )
        chain_args = ApiClient.get_chain_args(chain_name=chain_name.selected_value)
        args = {
            arg: rio.TextInput(label=arg, text=str(prompt.get(arg, "")))
            for arg in chain_args
            if arg != "user_input" or show_user_input
        }
        return {
            "chain": chain_name.selected_value,
            **{key: value.text for key, value in args.items()},
        }

    def command_selection(self, prompt: dict = {}, show_user_input: bool = True):
        agent_commands = ApiClient.get_extensions()
        available_commands = [
            command["friendly_name"]
            for commands in agent_commands
            for command in commands["commands"]
        ]
        command_name = rio.Dropdown(
            label="Select Command",
            options=available_commands,
            selected_value=prompt.get(
                "command_name", available_commands[0] if available_commands else ""
            ),
        )
        command_args = ApiClient.get_command_args(
            command_name=command_name.selected_value
        )
        args = {
            arg: rio.TextInput(label=arg, text=str(prompt.get(arg, "")))
            for arg in command_args
            if arg != "user_input" or show_user_input
        }
        return {
            "command_name": command_name.selected_value,
            "command_args": {key: value.text for key, value in args.items()},
        }

    def build(self) -> rio.Component:
        agent_action = rio.Dropdown(
            label="Action",
            options=["Create Agent", "Modify Agent", "Delete Agent"],
            selected_value="Create Agent",
        )

        if agent_action.selected_value == "Create Agent":
            agent_name = rio.TextInput("", label="Enter the agent name:")
        else:
            agent_names = [agent["name"] for agent in ApiClient.get_agents()]
            agent_name = rio.Dropdown(
                label="Select Agent",
                options=agent_names,
                selected_value=agent_names[0] if agent_names else "",
            )

        providers = self.get_providers_safe()
        agent_provider = rio.Dropdown(
            label="Select Provider",
            options=providers,
            selected_value=providers[0] if providers else "",
        )

        agent_settings = self.get_provider_settings_safe(agent_provider.selected_value)
        if not agent_settings:
            print(
                f"Warning: No settings found for provider {agent_provider.selected_value}"
            )
            agent_settings = {}

        selected_language_provider = rio.Dropdown(
            label="Language Provider",
            options=providers,
            selected_value=agent_settings.get("Language Provider", ""),
        )

        selected_vision_provider = rio.Dropdown(
            label="Vision Provider (Optional)",
            options=["None"] + providers,
            selected_value=agent_settings.get("Vision Provider", "None"),
        )

        selected_tts_provider = rio.Dropdown(
            label="Text to Speech Provider",
            options=providers,
            selected_value=agent_settings.get("Text to Speech Provider", ""),
        )

        selected_stt_provider = rio.Dropdown(
            label="Speech to Text Provider",
            options=providers,
            selected_value=agent_settings.get("Speech to Text Provider", ""),
        )

        selected_image_provider = rio.Dropdown(
            label="Image Generation Provider (Optional)",
            options=["None"] + providers,
            selected_value=agent_settings.get("Image Generation Provider", "None"),
        )

        selected_embedding_provider = rio.Dropdown(
            label="Embeddings Provider",
            options=providers,
            selected_value=agent_settings.get("Embeddings Provider", ""),
        )

        provider_settings = {}
        provider_settings = self.render_provider_settings(
            selected_language_provider.selected_value,
            agent_settings,
            provider_settings,
        )
        provider_settings = self.render_provider_settings(
            selected_vision_provider.selected_value,
            agent_settings,
            provider_settings,
        )
        provider_settings = self.render_provider_settings(
            selected_tts_provider.selected_value,
            agent_settings,
            provider_settings,
        )
        provider_settings = self.render_provider_settings(
            selected_stt_provider.selected_value,
            agent_settings,
            provider_settings,
        )
        provider_settings = self.render_provider_settings(
            selected_image_provider.selected_value,
            agent_settings,
            provider_settings,
        )
        provider_settings = self.render_provider_settings(
            selected_embedding_provider.selected_value,
            agent_settings,
            provider_settings,
        )

        try:
            extensions = ApiClient.get_extensions()
            multi_select_extension = MultiSelect(
                options=[
                    {
                        "name": ext.get("name", f"Extension_{i}"),
                        "display": ext.get(
                            "friendly_name", ext.get("name", f"Extension_{i}")
                        ),
                        "settings": ext.get("settings", []),
                    }
                    for i, ext in enumerate(extensions)
                ],
                selected=set(agent_settings.get("Extensions", [])),
            )
        except Exception as e:
            print(f"Error getting extensions: {str(e)}")
            multi_select_extension = MultiSelect(options=[], selected=set())

        helper_agent = rio.Dropdown(
            label="Helper Agent (Optional)",
            options=["None"] + [agent["name"] for agent in ApiClient.get_agents()],
            selected_value=agent_settings.get("Helper Agent", "None"),
        )

        chat_completions_mode = rio.Dropdown(
            label="Chat Completions Mode",
            options=["default", "prompt", "chain", "command"],
            selected_value=agent_settings.get("Chat Completions Mode", "default"),
        )

        prompt_settings_elements = [
            self.prompt_selection(prompt=agent_settings, show_user_input=False)
        ]

        chain_settings_elements = [
            self.chain_selection(prompt=agent_settings, show_user_input=False)
        ]

        command_settings_elements = [
            self.command_selection(prompt=agent_settings, show_user_input=False)
        ]

        command_variable = rio.TextInput(label="Command Variable", text="")

        save_button = rio.Button(
            "Save",
            on_press=lambda: asyncio.create_task(
                self.save_agent_settings(
                    agent_action.selected_value,
                    (
                        agent_name.text
                        if agent_action.selected_value == "Create Agent"
                        else agent_name.selected_value
                    ),
                    {
                        "Language Provider": selected_language_provider.selected_value,
                        "Vision Provider": selected_vision_provider.selected_value,
                        "Text to Speech Provider": selected_tts_provider.selected_value,
                        "Speech to Text Provider": selected_stt_provider.selected_value,
                        "Image Generation Provider": selected_image_provider.selected_value,
                        "Embeddings Provider": selected_embedding_provider.selected_value,
                        "Extensions": list(multi_select_extension.selected),
                        "Helper Agent": helper_agent.selected_value,
                        "Chat Completions Mode": chat_completions_mode.selected_value,
                        **(
                            self.prompt_selection(
                                prompt=agent_settings, show_user_input=False
                            )
                            if chat_completions_mode.selected_value == "prompt"
                            else {}
                        ),
                        **(
                            self.chain_selection(
                                prompt=agent_settings, show_user_input=False
                            )
                            if chat_completions_mode.selected_value == "chain"
                            else {}
                        ),
                        **(
                            self.command_selection(
                                prompt=agent_settings, show_user_input=False
                            )
                            if chat_completions_mode.selected_value == "command"
                            else {}
                        ),
                    },
                    command_variable.text,
                )
            ),
        )

        return rio.Column(
            rio.Markdown("# Agent Management"),
            agent_action,
            agent_name,
            rio.Markdown("## Select Providers"),
            rio.Row(
                rio.Column(
                    rio.Markdown("### Language Provider"),
                    selected_language_provider,
                    *[
                        component
                        for component in provider_settings.values()
                        if isinstance(component, rio.Component)
                    ],
                ),
                rio.Column(
                    rio.Markdown("### Vision Provider (Optional)"),
                    selected_vision_provider,
                    *(
                        [
                            component
                            for component in provider_settings.values()
                            if isinstance(component, rio.Component)
                        ]
                        if selected_vision_provider.selected_value != "None"
                        else [rio.Container(content=rio.Text(""))]
                    ),
                    rio.Markdown("### Text to Speech Provider"),
                    selected_tts_provider,
                    *[
                        component
                        for component in provider_settings.values()
                        if isinstance(component, rio.Component)
                    ],
                    rio.Markdown("### Speech to Text Provider"),
                    selected_stt_provider,
                    *[
                        component
                        for component in provider_settings.values()
                        if isinstance(component, rio.Component)
                    ],
                    rio.Markdown("### Image Generation Provider (Optional)"),
                    selected_image_provider,
                    *(
                        [
                            component
                            for component in provider_settings.values()
                            if isinstance(component, rio.Component)
                        ]
                        if selected_image_provider.selected_value != "None"
                        else [rio.Container(content=rio.Text(""))]
                    ),
                    rio.Markdown("### Embeddings Provider"),
                    selected_embedding_provider,
                ),
            ),
            rio.Markdown("## Configure Agent Settings"),
            rio.Row(
                rio.Column(
                    rio.Markdown("### Extensions"),
                    multi_select_extension,
                ),
                rio.Column(
                    rio.Markdown("### Helper Agent (Optional)"),
                    helper_agent,
                ),
            ),
            rio.Markdown("## Configure Chat Completions Mode"),
            chat_completions_mode,
            *(
                prompt_settings_elements
                if chat_completions_mode.selected_value == "prompt"
                else []
            ),
            *(
                chain_settings_elements
                if chat_completions_mode.selected_value == "chain"
                else []
            ),
            rio.Row(
                rio.Column(
                    *(
                        command_settings_elements
                        if chat_completions_mode.selected_value == "command"
                        else []
                    )
                ),
                rio.Column(
                    command_variable
                    if chat_completions_mode.selected_value == "command"
                    else rio.Container(content=rio.Text(""))
                ),
            ),
            save_button,
            (
                rio.Container(
                    content=rio.Text(
                        self.message,
                        style=rio.TextStyle(
                            fill=rio.Color.RED if self.is_error else rio.Color.GREEN
                        ),
                    )
                )
                if self.message
                else rio.Container(content=rio.Text(""))
            ),
        )
