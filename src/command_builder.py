import os
import json
import platform
from typing import Dict, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.theme import Theme
from rich.text import Text
from rich.style import Style
from rich.padding import Padding


class CommandBuilder:
    """
    A class to handle creation and management of command configurations.
    """

    def __init__(self, target_directory: str = "./prj_mem/"):
        self.target_directory = target_directory
        self.shell_type = "powershell" if platform.system() == "Windows" else "bash"
        self.console = Console(
            theme=Theme(
                {
                    "info": "cyan",
                    "warning": "yellow",
                    "error": "red bold",
                    "success": "green bold",
                }
            )
        )

    def display_header(self):
        """Display a header for the command builder."""
        header_text = Text()
        header_text.append("📝 ", style="bold yellow")
        header_text.append("Command Builder", style="bold blue")
        self.console.print(Panel(header_text, border_style="blue"))
        self.console.print()

    def get_valid_filename(self) -> Optional[Tuple[str, str]]:
        """
        Get and validate filename from user input.

        Returns:
            Tuple[str, str]: Tuple of (filename, full_path) if valid, None if cancelled
        """
        self.console.print(Panel("File Configuration", border_style="blue"))

        while True:
            file_name = Prompt.ask(
                "[cyan]What would you like to call this file?[/cyan]",
                console=self.console,
            ).strip()

            if not file_name:
                self.console.print(
                    "[error]Filename cannot be empty. Please try again.[/error]"
                )
                continue

            if not file_name.endswith(".json"):
                file_name += ".json"

            full_path = os.path.join(self.target_directory, file_name)

            if os.path.exists(full_path):
                override = Confirm.ask(
                    f"[warning]File {full_path} already exists. Do you want to override it?[/warning]",
                    console=self.console,
                )
                if not override:
                    continue

            self.console.print()
            return file_name, full_path

    def get_valid_command_path(self) -> Optional[str]:
        """
        Get and validate command path from user input.

        Returns:
            str: Valid command path or None if cancelled
        """
        self.console.print(Panel("Path Configuration", border_style="blue"))

        while True:
            self.console.print(
                Panel.fit(
                    "[info]Enter the full path for running commands.[/info]\n"
                    f"[dim]Current shell: [bold]{self.shell_type}[/bold][/dim]\n"
                    "[dim]Example: C:/Users/JohnDoe/project_name[/dim]",
                    title="Path Input",
                    border_style="cyan",
                )
            )

            command_path = Prompt.ask("[cyan]Path[/cyan]").strip()

            if not command_path:
                self.console.print(
                    "[error]Command path cannot be empty. Please try again.[/error]"
                )
                continue

            if not os.path.exists(command_path):
                self.console.print(
                    "[warning]Warning: The specified path does not exist.[/warning]"
                )
                self.console.print(
                    Panel.fit(
                        "1. Continue anyway\n2. Enter a different path",
                        border_style="yellow",
                    )
                )
                choice = Prompt.ask(
                    "Choose an option",
                    choices=["1", "2"],
                    default="2",
                    show_choices=False,
                    show_default=False,
                    console=self.console,
                )

                if choice == "2":
                    continue

            self.console.print()
            return command_path

    def collect_commands(self) -> Dict[str, str]:
        """
        Collect commands from user input.

        Returns:
            Dict[str, str]: Dictionary of collected commands
        """
        commands = {}
        command_count = 0
        # Main instruction text
        main_text = Text.from_markup(
            "[bold cyan]Command Input Instructions[/bold cyan]\n\n"
            "➊ Enter your commands one at a time below\n"
            "➋ Commands should be relative to your entered path\n"
            "➌ Type 'X' when you're finished\n"
        )

        # Example section
        examples = Text.from_markup(
            "\n[bold yellow]Examples:[/bold yellow]\n"
            "✓ nodemon ./node_js_project/server.js\n"
            "✓ python3 ./scripts/main.py\n"
            "✓ npm start\n"
        )

        # Tips section
        tips = Text.from_markup(
            "\n[bold green]Tips:[/bold green]\n"
            "• Use ./ to specify relative paths\n"
            "• Make sure the file exists in the specified location\n"
            "• Commands are case-sensitive\n"
        )

        # Combine all sections with padding
        content = Padding(Text.assemble(main_text, examples, tips), (1, 2))
        self.console.print(
            Panel(
                content,
                title="[bold white]Command Input Guide[/bold white]",
                subtitle="[italic]Type 'X' to finish[/italic]",
                border_style="blue",
                highlight=True,
                padding=(1, 2),
            )
        )

        while True:
            command_prompt = Text()
            command_prompt.append(f"\nCommand {command_count + 1}", style="bold cyan")
            command_prompt.append(" (type 'X' to finish): ", style="dim")

            enter_command = Prompt.ask(command_prompt).strip()

            if enter_command.upper() == "X":
                if command_count == 0:
                    if not Confirm.ask(
                        "[warning]No commands have been added. Are you sure you want to save an empty command file?[/warning]",
                        console=self.console,
                    ):
                        continue
                break

            if not enter_command:
                self.console.print(
                    "[error]Command cannot be empty. Please try again.[/error]"
                )
                continue

            commands[f"command_{command_count}"] = enter_command
            command_count += 1

        return commands

    def save_commands(
        self, full_path: str, command_path: str, commands: Dict[str, str]
    ) -> bool:
        """
        Save commands to JSON file.

        Args:
            full_path (str): Path to save the JSON file
            command_path (str): Path for running commands
            commands (Dict[str, str]): Dictionary of commands to save

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            command_builder = {
                "path": command_path,
                "shell_type": self.shell_type,
                "commands": commands,
            }

            with open(full_path, "w") as json_file:
                json.dump(command_builder, json_file, indent=4)

            self.console.print(
                Panel(
                    f"[success]Successfully saved {len(commands)} command(s) to:[/success]\n"
                    f"[dim]{full_path}[/dim]",
                    border_style="green",
                )
            )
            return True

        except Exception as e:
            self.console.print(f"[error]Error saving commands: {str(e)}[/error]")
            return False


def create_new_command() -> bool:
    """
    Create new commands for the command builder and save them to a file.

    Returns:
        bool: True if commands were successfully saved, False otherwise
    """
    try:
        builder = CommandBuilder()
        builder.display_header()

        # Get valid filename
        filename_result = builder.get_valid_filename()
        if not filename_result:
            return False
        _, full_path = filename_result

        # Get valid command path
        command_path = builder.get_valid_command_path()
        if not command_path:
            return False

        # Collect commands
        commands = builder.collect_commands()

        # Save commands
        return builder.save_commands(full_path, command_path, commands)

    except KeyboardInterrupt:
        builder.console.print("\n[warning]Operation cancelled by user.[/warning]")
        return False
    except Exception as e:
        builder.console.print(
            f"\n[error]An unexpected error occurred: {str(e)}[/error]"
        )
        return False


if __name__ == "__main__":
    create_new_command()
