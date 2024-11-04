import subprocess
import shlex
import platform
import psutil
from pathlib import Path
from typing import List, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.style import Style
from rich.theme import Theme


class CommandRunner:
    def __init__(
        self,
        directory: str = "./prj_mem/",
        path: str = "",
        processes: List[subprocess.Popen] = None,
        shell_type: str = "",
    ):
        """Initialize CommandRunner with the specified parameters.

        Args:
            directory (str): Working directory path
            path (str): Additional path information
            processes (List[subprocess.Popen]): List of running processes
            shell_type (str): Type of shell to use ('powershell' or 'bash')
        """
        self.directory = Path(directory)
        self.processes = processes or []
        self.command_names: List[str] = []
        self.path = path
        self.shell_type = shell_type.lower()

        # Custom theme for consistent styling
        custom_theme = Theme(
            {
                "info": "cyan",
                "warning": "yellow",
                "error": "red bold",
                "success": "green bold",
                "command": "blue",
            }
        )
        self.console = Console(theme=custom_theme)

    def _format_command(self, command: str) -> str:
        """Format command based on shell type.

        Args:
            command (str): Command to format

        Returns:
            str: Formatted command
        """
        if self.shell_type == "powershell":
            return f'powershell.exe -Command "{command}"'
        elif self.shell_type == "bash":
            return f"/bin/bash -c {shlex.quote(command)}"
        else:
            raise ValueError(
                self.console.print(
                    "[error]Unsupported shell type. Use 'powershell' or 'bash'.[/error]"
                )
            )

    def run_command(self, command: str) -> Optional[subprocess.Popen]:
        """Execute a command in the specified shell.

        Args:
            command (str): Command to execute

        Returns:
            Optional[subprocess.Popen]: Process object if successful, None otherwise
        """
        formatted_command = self._format_command(command)

        self.console.print("[info]Executing command...[/info]")
        try:
            process = subprocess.Popen(
                formatted_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=True,
                creationflags=(
                    subprocess.CREATE_NEW_CONSOLE
                    if platform.system() == "Windows"
                    else 0
                ),
            )
            self.console.print("[success]Command executed successfully[/success]")
            return process
        except Exception as e:
            self.console.print(
                Panel(
                    Text(f"Failed to start process: {str(e)}", style="error"),
                    title="Error",
                    border_style="red",
                )
            )
            return None

    def setup_servers(
        self, commands_list: List[Tuple[str, str]]
    ) -> Tuple[Optional[List[subprocess.Popen]], Optional[List[str]]]:
        """Set up servers with the provided commands.

        Args:
            commands_list (List[Tuple[str, str]]): List of (process_name, command) tuples

        Returns:
            Tuple[Optional[List[subprocess.Popen]], Optional[List[str]]]: Tuple of processes and command names
        """
        commands = []
        path = Path(self.path)

        # Create table for command visualization
        table = Table(title="Server Setup Commands")
        table.add_column("Process Name", style="cyan")
        table.add_column("Command", style="green")

        if self.shell_type == "powershell":
            path = str(path).replace("/", "\\")
            for process_name, process in commands_list:
                process = process.replace("/", "\\")
                command = f'Set-Location "{path}"; {process}'
                commands.append((process_name, command))
                table.add_row(process_name, command)
        elif self.shell_type == "bash":
            for process_name, process in commands_list:
                command = f"cd ~/{path} && {process}"
                commands.append((process_name, command))
                table.add_row(process_name, command)
        else:
            self.console.print(
                "[error]Unsupported shell type. Use 'powershell' or 'bash'.[/error]"
            )
            return None, None

        self.console.print(table)
        self.console.print("[info]Starting servers...[/info]")

        for name, cmd in commands:
            self.console.print(f"[info]Starting {name}...[/info]")
            process = self.run_command(cmd)
            if process is not None:
                self.command_names.append(name)
                self.processes.append(process)
                self.console.print(f"[success]Successfully started: {name}[/success]")
            else:
                self.console.print(
                    f"[warning]Warning: [{name}] Failed to start.[/warning]"
                )

        if not self.processes:
            self.console.print(
                Panel(
                    Text("No servers started. Terminating.", style="error"),
                    title="Error",
                    border_style="red",
                )
            )
            return None, None

        # Show summary
        summary = Table(title="Server Setup Summary")
        summary.add_column("Status", style="cyan")
        summary.add_column("Count", style="green")
        summary.add_row("Total Commands", str(len(commands)))
        summary.add_row("Successfully Started", str(len(self.processes)))
        summary.add_row("Failed", str(len(commands) - len(self.processes)))
        self.console.print(summary)

        return self.processes, self.command_names
