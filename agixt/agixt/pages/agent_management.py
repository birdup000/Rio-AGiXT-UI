from __future__ import annotations
from agixtsdk import AGiXTSDK
from dataclasses import KW_ONLY, field
import rio

from typing import *  # type: ignore

base_uri = "http://localhost:7437"
api_key = "your_agixt_api_key"

ApiClient = AGiXTSDK(base_uri=base_uri, api_key=api_key)

def prompt_selection(prompt, show_user_input):
    # Implement this function based on your requirements
    return {}

def chain_selection(prompt, show_user_input):
    # Implement this function based on your requirements
    return {}

def command_selection(prompt, show_user_input):
    # Implement this function based on your requirements
    return {}

class AgentManagement(rio.Component):
    """
    Agent Management
    """

    def render_provider_settings(self, provider_name, agent_settings, provider_settings):
        settings = ApiClient.get_provider_settings(provider_name=provider_name)
        for key, value in settings.items():
            if key in provider_settings:
                # Use existing provider settings if available
                settings[key] = provider_settings[key]
            else:
                # Create new provider settings
                settings[key] = rio.TextInput(
                    str(agent_settings.get(key, value)),
                    label=f"{key}:",
                )
        provider_settings.update(settings)
        return provider_settings

    def build(self) -> rio.Component:
        def log_error(message: str):
            print(f"Error: {message}")  # Simple logging function for debugging

        try:
            agents = ApiClient.get_agents()
            if isinstance(agents, str):
                raise TypeError("Response from get_agents() is a string, expected a list of dictionaries.")
        except Exception as e:
            log_error(f"Error fetching agents: {e}")
            agents = []

        try:
            providers = ApiClient.get_providers()
        except Exception as e:
            log_error(f"Error fetching providers: {e}")
            providers = []

        try:
            extensions = ApiClient.get_extensions()
            if isinstance(extensions, str):
                raise TypeError("Response from get_extensions() is a string, expected a list of dictionaries.")
        except Exception as e:
            log_error(f"Error fetching extensions: {e}")
            extensions = []

        if agents:
            selected_agent = agents[0].get("name", "Select an agent")
        else:
            selected_agent = "Select an agent"
            agents = [{"name": "No agents available"}]

        selected_provider = providers[0] if providers else "Select a provider"

        def handle_agent_change(value):
            nonlocal selected_agent
            selected_agent = value

        def handle_provider_change(value):
            nonlocal selected_provider
            selected_provider = value

        agent_action = rio.Dropdown(
            label="Action",
            options=["Create Agent", "Modify Agent", "Delete Agent"],
            selected_value="Create Agent",  # Set a default selected value
        )

        if agent_action.selected_value == "Create Agent":
            agent_name = rio.TextInput("", label="Enter the agent name:")
        else:
            agent_names = [agent.get("name", "Unnamed agent") for agent in agents]
            agent_name = rio.Dropdown(
                label="Select an agent:",
                options=agent_names,
                selected_value=agent_names[0] if agent_names else "",  # Set a default selected value
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
            selected_value=agent_settings.get("provider", language_providers[0] if language_providers else ""),  # Set a default selected value
        )
        provider_settings = self.render_provider_settings(
            selected_language_provider.selected_value,
            agent_settings,
            provider_settings,
        )

        vision_providers = ["None"] + (ApiClient.get_providers_by_service("vision") or [])
        selected_vision_provider = rio.Dropdown(
            label="Select vision provider:",
            options=vision_providers,
            selected_value=agent_settings.get("vision_provider", "None"),
        )
        if selected_vision_provider.selected_value != "None":
            provider_settings = self.render_provider_settings(
                selected_vision_provider.selected_value,
                agent_settings,
                provider_settings,
            )

        tts_providers = ["None"] + (ApiClient.get_providers_by_service("tts") or [])
        selected_tts_provider = rio.Dropdown(
            label="Select text to speech provider:",
            options=tts_providers,
            selected_value=agent_settings.get("tts_provider", "None"),
        )
        provider_settings = self.render_provider_settings(
            selected_tts_provider.selected_value,
            agent_settings,
            provider_settings,
        )

        stt_providers = ApiClient.get_providers_by_service("transcription") or []
        selected_stt_provider = rio.Dropdown(
            label="Select speech to text provider:",
            options=stt_providers if stt_providers else ["No providers"],
            selected_value=agent_settings.get("transcription_provider", stt_providers[0] if stt_providers else ""),  # Set a default selected value
        )
        provider_settings = self.render_provider_settings(
            selected_stt_provider.selected_value,
            agent_settings,
            provider_settings,
        )

        image_providers = ["None"] + (ApiClient.get_providers_by_service("image") or [])
        selected_img_provider = agent_settings.get("image_provider", "None")
        selected_image_provider = rio.Dropdown(
            label="Select image generation provider:",
            options=image_providers,
            selected_value=selected_img_provider,
        )
        if selected_image_provider.selected_value != "None":
            provider_settings = self.render_provider_settings(
                selected_image_provider.selected_value,
                agent_settings,
                provider_settings,
            )

        embedding_providers = ApiClient.get_providers_by_service("embeddings") or []
        selected_embedding_provider = rio.Dropdown(
            label="Select embeddings provider:",
            options=embedding_providers if embedding_providers else ["No providers"],
            selected_value=agent_settings.get("embeddings_provider", embedding_providers[0] if embedding_providers else ""),  # Set a default selected value
        )

        # Create a dictionary to store the selected state of each extension
        selected_extensions = {extension["extension_name"]: False for extension in extensions}

        # Update the selected state based on enabled commands
        for extension in extensions:
            for command in extension["commands"]:
                if agent_commands.get(command["friendly_name"], False):
                    selected_extensions[extension["extension_name"]] = True
                    break

        # Create a list of Switch components for each extension
        extension_switches = [
            rio.Column(
                rio.Text(extension["extension_name"]),
                rio.Switch(
                    is_on=selected_extensions.get(extension["extension_name"], False),
                    on_change=lambda event, ext=extension: selected_extensions.update({ext["extension_name"]: event.is_on}),
                ),
            )
            for extension in extensions
        ]

        extension_settings = {
            setting: rio.TextInput(
                str(agent_settings.get(setting, "")),
                label=f"{setting}:",
            )
            for extension in extensions
            if selected_extensions.get(extension["extension_name"], False)
            for setting in extension["settings"]
        }

        selected_commands = [
            command["friendly_name"]
            for extension in extensions
            if selected_extensions.get(extension["extension_name"], False)
            for command in extension["commands"]
            if agent_commands.get(command["friendly_name"], False)
        ]

        helper_agent = rio.Dropdown(
            label="Select Helper Agent (Your agent may ask the selected one for help when it needs something.)",
            options=[agent.get("name", "Unnamed agent") for agent in agents],
            selected_value=agent_config.get("helper_agent_name", ""),
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
            prompt_settings_elements = [rio.TextInput(value=str(prompt_settings[key]), label=key) for key in prompt_settings]

        if chat_completions_mode.selected_value == "chain":
            chain_settings = chain_selection(prompt=agent_settings, show_user_input=False)
            chain_settings_elements = [rio.TextInput(value=str(chain_settings[key]), label=key) for key in chain_settings]

        if chat_completions_mode.selected_value == "command":
            command_settings = command_selection(prompt=agent_settings, show_user_input=False)
            command_settings_elements = [rio.TextInput(value=str(command_settings[key]), label=key) for key in command_settings]
            if command_settings and "command_args" in command_settings:
                command_variable = rio.Dropdown(
                    label="Select Command Variable",
                    options=[""] + list(command_settings["command_args"].keys()),
                    selected_value=agent_settings.get("command_variable", ""),
                )

        def save_agent_settings():
            settings = {
                "provider": selected_language_provider.selected_value,
                **{key: value.value for key, value in provider_settings.items()},
                "vision_provider": selected_vision_provider.selected_value,
                "transcription_provider": selected_stt_provider.selected_value,
                "translation_provider": selected_stt_provider.selected_value,
                "tts_provider": selected_tts_provider.selected_value if selected_tts_provider.selected_value != "None" else "None",
                "image_provider": selected_image_provider.selected_value if selected_image_provider.selected_value != "None" else "None",
                "embeddings_provider": selected_embedding_provider.selected_value,
                "helper_agent_name": helper_agent.selected_value,
                **{key: value.value for key, value in extension_settings.items()},
                "mode": chat_completions_mode.selected_value,
            }

            if chat_completions_mode.selected_value == "prompt":
                settings.update({key: element.value for key, element in zip(prompt_settings, prompt_settings_elements)})

            if chat_completions_mode.selected_value == "chain":
                settings.update({key: element.value for key, element in zip(chain_settings, chain_settings_elements)})

            if chat_completions_mode.selected_value == "command":
                settings.update({key: element.value for key, element in zip(command_settings, command_settings_elements)})
                settings["command_variable"] = command_variable.selected_value if command_variable else ""

            commands = {command: True for command in selected_commands}

            if agent_action.selected_value == "Create Agent":
                response = ApiClient.add_agent(
                    agent_name=agent_name.value, settings=settings, commands=commands
                )
                print(f"Agent '{agent_name.value}' created.")
            elif agent_action.selected_value == "Modify Agent":
                response = ApiClient.update_agent_settings(
                    agent_name=agent_name.value, settings=settings
                )
                response = ApiClient.update_agent_commands(
                    agent_name=agent_name.value, commands=commands
                )
                print(f"Agent '{agent_name.value}' updated.")
            elif agent_action.selected_value == "Delete Agent":
                response = ApiClient.delete_agent(agent_name.value)
                print(f"Agent '{agent_name.value}' deleted.")

        return rio.Column(
            rio.Column(
                rio.Markdown(
                    """
# Agent Management
""",
                    width=60,
                    margin_bottom=4,
                    align_x=0.5,
                    align_y=0,
                )
            ),
            rio.Column(agent_action),
            rio.Column(agent_name),
            rio.Column(
                rio.Markdown("## Select Providers"),
                rio.Row(
                    rio.Column(
                        rio.Markdown("### Language Provider"),
                        selected_language_provider,
                        *provider_settings.values(),
                    ),
                    rio.Column(
                        rio.Markdown("### Vision Provider (Optional)"),
                        selected_vision_provider,
                        *(provider_settings.values() if selected_vision_provider.selected_value != "None" else [rio.Container(content=rio.Text(""))]),
                        rio.Markdown("### Text to Speech Provider"),
                        selected_tts_provider,
                        *provider_settings.values(),
                        rio.Markdown("### Speech to Text Provider"),
                        selected_stt_provider,
                        *provider_settings.values(),
                        rio.Markdown("### Image Generation Provider (Optional)"),
                        selected_image_provider,
                        *(provider_settings.values() if selected_image_provider.selected_value != "None" else [rio.Container(content=rio.Text(""))]),
                        rio.Markdown("### Embeddings Provider"),
                        selected_embedding_provider,
                    ),
                ),
            ),
            rio.Column(
                rio.Markdown("## Configure Chat Completions Mode"),
                chat_completions_mode,
                *prompt_settings_elements if chat_completions_mode.selected_value == "prompt" else [],
                *chain_settings_elements if chat_completions_mode.selected_value == "chain" else [],
                rio.Row(
                    rio.Column(*command_settings_elements if chat_completions_mode.selected_value == "command" else []),
                    rio.Column(command_variable if chat_completions_mode.selected_value == "command" else rio.Container(content=rio.Text(""))),
                ),
            ),
            rio.Column(
                rio.Markdown("## Agent Extensions"),
                rio.Row(
                    rio.Column(
                        rio.Markdown("### Extensions"),
                        rio.Dropdown(options=[ext for ext in selected_extensions.keys()], selected_value=next(iter(selected_extensions), "No extensions")),
                        *extension_switches,
                        *extension_settings.values(),
                    ),
                    rio.Column(
                        rio.Markdown("### Helper Agent (Optional)"),
                        helper_agent,
                    ),
                ),
            ),
            rio.Button(
                "Save Agent Settings",
                on_press=lambda: save_agent_settings(),
            ),
        )