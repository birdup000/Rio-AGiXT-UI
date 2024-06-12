import rio

class ChainManagement(rio.Component):
    chain_name: str = "Example Chain"
    steps: list = [
        {'agent_name': 'Agent 1', 'prompt_type': 'Chain'},
        {'agent_name': 'Agent 2', 'prompt_type': 'Prompt'}
    ]
    selected_prompt_type: str = "Chain"
    selected_step_index: int = 0

    def build(self):
        return rio.Column(
            self.create_header(),
            self.create_step_list(),
            self.create_step_editor(),
            rio.Row(  # Placing the buttons in a row at the bottom
                rio.Button(
                    content="Save",
                    on_press=self.on_save,
                    width=5,  # Adjust the width of the button
                    height=2  # Adjust the height of the button
                ),
                rio.Button(
                    content="Load",
                    on_press=self.on_load,
                    width=5,  # Adjust the width of the button
                    height=2  # Adjust the height of the button
                ),
                align_x=0.5  # Align the row to the center horizontally
            )
        )
    def create_header(self):
        return rio.Row(
            rio.TextInput(
                text=self.chain_name,
                label="Chain Name",
                on_change=self.on_chain_name_change,
                width=10  # Adjust the width of the text input if needed
            ),

        )

    
    def on_save(self):
        if self.validate_chain():
            # Implement save logic
            pass

    def on_load(self):
        # Implement load logic
        pass

    def on_step_number_change(self, event):
        self.selected_step_index = event.selected_value - 1
        self.update()
    
    def on_agent_name_change(self, event):
        self.steps[self.selected_step_index]["agent_name"] = event.text
        self.update()
    
    def on_prompt_type_change(self, event):
        self.selected_prompt_type = event.selected_value
        self.update()

    def on_chain_change(self, event):
        self.steps[self.selected_step_index]["chain"] = event.text
        self.update()
    
    def on_input_change(self, event):
        self.steps[self.selected_step_index]["input"] = event.text
        self.update()

    def create_step_list(self):
        step_items = [self.create_step_item(step, index) for index, step in enumerate(self.steps)]
        return rio.ListView(*step_items)

    def create_step_item(self, step, index):
        return rio.SimpleListItem(
            text=f"Step {index + 1}",
            secondary_text=f"{step['agent_name']} - {step['prompt_type']}",
            key=f"step-item-{index}",
            right_child=rio.Row(
                rio.Button(content="Edit", on_press=lambda: self.edit_step(index), width=2, height=1),
                rio.Button(content="Delete", on_press=lambda: self.delete_step(index), width=2, height=1),
                rio.Button(content="Move Up", on_press=lambda: self.move_step_up(index), width=2, height=1),
                rio.Button(content="Move Down", on_press=lambda: self.move_step_down(index), width=2, height=1),
                rio.Button(content="Duplicate", on_press=lambda: self.duplicate_step(index), width=2, height=1),
                spacing=0.2  # Adjust spacing between buttons
            )
        )

    def create_step_editor(self):
        if not self.steps:
            return rio.Text("No steps available to edit.")

        step = self.steps[self.selected_step_index]
        return rio.Column(
            rio.Dropdown(
                options=[i + 1 for i in range(len(self.steps))],
                label="Step Number",
                selected_value=self.selected_step_index + 1,
                on_change=self.on_step_number_change
            ),
            rio.TextInput(
                text=step.get("agent_name", ""),
                label="Agent Name",
                on_change=self.on_agent_name_change
            ),
            rio.Dropdown(
                options=["Chain", "Prompt", "Command"],
                label="Prompt Type",
                selected_value=self.selected_prompt_type,
                on_change=self.on_prompt_type_change
            ),
            self.create_prompt_editor()
        )

    def create_prompt_editor(self):
        if self.selected_prompt_type == "Chain":
            return self.create_chain_prompt_editor()
        elif self.selected_prompt_type == "Prompt":
            return self.create_prompt_prompt_editor()
        elif self.selected_prompt_type == "Command":
            return self.create_command_prompt_editor()
        return rio.Text("Select a prompt type to edit.")

    def create_chain_prompt_editor(self):
        step = self.steps[self.selected_step_index]
        return rio.Column(
            rio.TextInput(
                text=step.get("chain", ""),
                label="Chain",
                on_change=self.on_chain_change
            ),
            rio.TextInput(
                text=step.get("input", ""),
                label="Input",
                on_change=self.on_input_change
            )
        )

    def create_prompt_prompt_editor(self):
        step = self.steps[self.selected_step_index]
        return rio.Column(
            rio.TextInput(
                text=step.get("prompt_name", ""),
                label="Prompt Name",
                on_change=self.on_prompt_name_change
            ),
            rio.TextInput(
                text=step.get("introduction", ""),
                label="Introduction",
                on_change=self.on_introduction_change
            ),
            rio.Switch(
                is_on=step.get("web_search", False),
                label="Web Search",
                on_change=self.on_web_search_change
            ),
            rio.NumberInput(
                value=step.get("web_search_depth", 0),
                label="Web Search Depth",
                on_change=self.on_web_search_depth_change
            ),
            rio.NumberInput(
                value=step.get("context_results", 0),
                label="Context Results",
                on_change=self.on_context_results_change
            )
        )

    def create_command_prompt_editor(self):
        step = self.steps[self.selected_step_index]
        return rio.Column(
            rio.TextInput(
                text=step.get("command_name", ""),
                label="Command Name",
                on_change=self.on_command_name_change
            ),
            rio.TextInput(
                text=step.get("agent", ""),
                label="Agent",
                on_change=self.on_agent_change
            ),
            rio.TextInput(
                text=step.get("primary_objective", ""),
                label="Primary Objective",
                on_change=self.on_primary_objective_change
            ),
            rio.TextInput(
                text=step.get("tasks", ""),
                label="Numbered List of Tasks",
                on_change=self.on_tasks_change
            ),
            rio.TextInput(
                text=step.get("chain_description", ""),
                label="Short Chain Description",
                on_change=self.on_chain_description_change
            ),
            rio.Switch(
                is_on=step.get("smart_chain", False),
                label="Smart Chain",
                on_change=self.on_smart_chain_change
            ),
            rio.Switch(
                is_on=step.get("researching", False),
                label="Researching",
                on_change=self.on_researching_change
            )
        )

    # Event handlers...

    def on_chain_name_change(self, event):
        self.chain_name = event.text
        self.update()

    # Other event handler methods...

    def validate_chain(self):
        # Implement validation logic
        return True

