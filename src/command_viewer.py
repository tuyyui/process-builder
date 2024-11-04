import os
import json
from typing import Dict, List
import keyboard
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class CommandViewer:
    def __init__(self, directory: str = "./prj_mem/"):
        """
        Initialize the CommandViewer with the target directory.

        Args:
            directory (str): Directory containing JSON command files
        """
        self.directory = directory
        self.console = Console()
        self.current_file_index = 0
        self.current_command_index = 0
        self.files = []
        self.current_commands = {}

    def load_command_files(self) -> List[str]:
        """
        Load all JSON files from the directory.

        Returns:
            List[str]: List of JSON file names
        """
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"Directory {self.directory} does not exist")

        self.files = [f for f in os.listdir(self.directory) if f.endswith(".json")]
        return self.files

    def load_commands_from_file(self, filename: str) -> Dict:
        """
        Load commands from a specific JSON file.

        Args:
            filename (str): Name of the JSON file

        Returns:
            Dict: Dictionary containing the commands
        """
        file_path = os.path.join(self.directory, filename)
        with open(file_path, "r") as f:
            return json.load(f)

    def clear_screen(self):
        """Clear the terminal screen."""
        self.console.clear()

    def display_current_view(self):
        """Display the current command view with navigation information."""
        self.clear_screen()

        if not self.files:
            self.console.print("[red]No command files found in directory[/red]")
            return

        # Display current file info
        current_file = self.files[self.current_file_index]
        self.console.print(
            f"\n[bold blue]File ({self.current_file_index + 1}/{len(self.files)}): "
            f"{current_file}[/bold blue]\n"
        )

        try:
            # Load and display commands from current file
            command_data = self.load_commands_from_file(current_file)
            commands = command_data.get("commands", {})
            path = command_data.get("path", "N/A")
            shell_type = command_data.get("shell_type", "N/A")

            # Display file metadata
            self.console.print(
                Panel(
                    f"Path: {path}\nShell Type: {shell_type}",
                    title="Configuration",
                    border_style="blue",
                )
            )

            # Display commands
            if not commands:
                self.console.print("\n[yellow]No commands found in this file[/yellow]")
                return

            command_items = list(commands.items())
            current_command = command_items[self.current_command_index]

            # Create command display
            command_text = Text()
            for idx, (cmd_key, cmd_value) in enumerate(command_items):
                if idx == self.current_command_index:
                    command_text.append(
                        f"> {cmd_key}: {cmd_value}\n", style="bold green"
                    )
                else:
                    command_text.append(f"  {cmd_key}: {cmd_value}\n", style="dim")

            self.console.print(
                Panel(
                    command_text,
                    title=f"Commands ({self.current_command_index + 1}/{len(commands)})",
                    border_style="green",
                )
            )

            # Display navigation help
            self.console.print("\n[dim]Navigation:[/dim]")
            self.console.print(
                "[dim]↑/↓: Navigate commands | ←/→: Navigate files | Q: Quit | R: Run Command [/dim] | [yellow] L: Run All Commands [/yellow]"
            )

        except Exception as e:
            self.console.print(f"[red]Error loading commands: {str(e)}[/red]")

    def _navigate_commands(self, direction):
        """Navigate between commands in the current file."""
        command_data = self.load_commands_from_file(self.files[self.current_file_index])
        commands = command_data.get("commands", {})
        if commands:
            self.current_command_index = (self.current_command_index + direction) % len(
                commands
            )

    def _navigate_files(self, direction):
        """Navigate between json files."""
        self.current_file_index = (self.current_file_index + direction) % len(
            self.files
        )
        self.current_command_index = 0

    def _handle_list_command(self):
        """Handle 'L' key press - return all commands with metadata.
        Returns dict with commands list and metadata
        """
        command_data = self.load_commands_from_file(self.files[self.current_file_index])
        return {
            "commands": list(command_data.get("commands", {}).items()),
            "path": command_data.get("path"),
            "shell_type": command_data.get("shell_type"),
        }

    def _handle_run_command(self):
        """
        Handle 'R' key press - return current command with metadata.
        Returns dict with single command and metadata.
        """
        command_data = self.load_commands_from_file(self.files[self.current_file_index])
        commands = command_data.get("commands", {})
        command_items = list(commands.items())
        return {
            "command": command_items[self.current_command_index],
            "path": command_data.get("path"),
            "shell_type": command_data.get("shell_type"),
        }

    def run(self):
        """
        Run the command viewer with keyboard navigation.

        Returns:
            List | Tuple | None: Selected commands to run, or None if viewer is closed.
                - List of all commands when 'L' is pressed
                - Tuple of current command when 'R' is pressed
                - None when viewer is closed or error occurs
        """
        try:

            if not (self.load_command_files()):

                self.console.print("[red]No command files found[/red]")
                return None

            self.display_current_view()

            # Key mapping for better readability and maintenance
            KEY_ACTIONS = {
                "q": lambda: "quit",
                "l": self._handle_list_command,
                "r": self._handle_run_command,
                "up": lambda: self._navigate_commands(-1),
                "down": lambda: self._navigate_commands(1),
                "left": lambda: self._navigate_files(-1),
                "right": lambda: self._navigate_files(1),
            }

            while True:
                event = keyboard.read_event(suppress=True)
                if event.event_type != "down":
                    continue

                action = KEY_ACTIONS.get(event.name.lower())
                if not action:
                    continue

                result = action()
                if result == "quit":
                    break
                if result is not None:
                    return result

                self.display_current_view()

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Viewer closed[/yellow]")
            return None
        except Exception as e:
            self.console.print(f"\n[red]An error occurred: {e}[/red]")
            return None
        finally:
            self.clear_screen()
