import subprocess
import threading
import time
import psutil
import argparse
from command_builder import CommandBuilder
from command_viewer import CommandViewer
from command_runner import CommandRunner
import sys
from rich.console import Console
from rich.live import Live
from typing import List, Optional, Dict, Tuple
from rich.table import Table


def read_output(process, name):
    """
    Streams the output of a given process line-by-line and labels it with a specified name.

    Args:
        process (subprocess.Popen): The process from which to read output.
        name (str): A label or identifier for the process, used in output.
    """
    if process is None:
        print(f"[{name}] Process not started.")
        return
    try:
        for line in process.stdout:
            if line:
                print(f"[{name}] {line.strip()}")
            else:
                break
    except Exception as e:
        print(f"[{name}] Error reading output: {e}")
    finally:
        if process.stdout:
            process.stdout.close()


def kill_process_tree(pid):
    """
    Terminates a process and all of its child processes.

    Args:
        pid (int): The process ID of the parent process to terminate.

    The function first attempts to terminate all child processes recursively,
    then the parent process itself. If any processes remain alive after the
    initial termination attempt, it forcefully kills them. Handles exceptions
    for non-existent, inaccessible, or zombie processes to ensure robust
    termination.
    """

    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # Terminate child processes
        for child in children:
            try:
                child.terminate()
            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
            ) as e:
                print(f"Error terminating child process {child.pid}: {e}")

        # Terminate parent process
        try:
            parent.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error terminating parent process {parent.pid}: {e}")

        # Wait for processes to terminate
        try:
            alive_processes = [
                p for p in children + [parent] if psutil.pid_exists(p.pid)
            ]
            gone, alive = psutil.wait_procs(alive_processes, timeout=3)
            for p in alive:
                try:
                    p.kill()
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ) as e:
                    print(f"Error killing process {p.pid}: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Error waiting for processes to terminate: {e}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
        print(f"Error accessing process {pid}: {e}")


def handle_process_termination(pid, return_code):
    """
    Handles return code on termination of a process

    Args:
        pid (int): the id of a process
        return_code (int): The code of a terminated process.
    """
    console = Console()

    if return_code == 0:
        console.print(f"[green]Process {pid} terminated normally[/green]")
    elif return_code < 0:
        console.print(f"[red]Process {pid} terminated by signal -{return_code}[/red]")
    else:
        console.print(
            f"[yellow]Process {pid} terminated with non-zero code {return_code} - possible error[/yellow]"
        )


def kill_servers(processes):
    """
    Terminates a list of server processes and their child processes.

    Args:
        processes (list): A list of subprocess.Popen objects representing the
                          server processes to be terminated.

    For each active process in the list, this function:
    - Terminates the entire process tree, including child processes, by calling
      `kill_process_tree`.
    - Closes any open `stdout` file descriptors for cleanup.
    - Waits for the process to terminate, with a timeout to prevent hanging.

    If a process does not terminate within the timeout, it attempts a forced
    kill. Logs any errors encountered during cleanup and ensures all processes
    are terminated before exiting.
    """
    console = Console()
    if processes:
        for process in processes:
            if not isinstance(process, subprocess.Popen):
                raise TypeError(
                    f"Excepted subprocess.Popen object, got {type(process)}"
                )

            if (
                process is not None and process.poll() is None
            ):  # Process is still running
                try:
                    console.print(f"\n[red] Killing process {process.pid}")
                    kill_process_tree(process.pid)
                    # Clean up file descriptors
                    if process.stdout:
                        process.stdout.close()

                    return_code = process.wait(timeout=5)  # Wait for process to finish
                    handle_process_termination(process.pid, return_code)
                except (
                    psutil.NoSuchProcess,
                    subprocess.TimeoutExpired,
                    psutil.AccessDenied,
                ) as e:
                    console.print(f"[red]Error during cleanup: {e} [/red]")
                    try:
                        process.kill()  # Force kill if necessary
                        process.wait()
                    except Exception as e:
                        console.print(f"[red]Failed to kill process: {e} [/red]")
    else:
        console.print("[yellow] no processes to terminate [/yellow]")
    console.print("[yellow]Servers have been terminated.[/yellow]")


def create_new_command() -> bool:
    """
    Create new commands for the command builder and save them to a file.

    Returns:
        bool: True if commands were successfully saved, False otherwise
    """
    try:
        builder = CommandBuilder()

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
        print("\nOperation cancelled by user.")
        return False
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}")
        return False


def execute_commands():
    """
    Retrieve the selected command for execution from the command viewer.

    Returns:
        dict or None: The selected command, typically containing keys like
                      'path', 'shell_type', and 'commands' (or similar).
                      Returns None if no command is selected or an error occurs.
    """
    try:
        viewer = CommandViewer()
        selected_command = viewer.run()

        # Validate selected_command structure
        if not selected_command or not isinstance(selected_command, dict):
            print("Error: No valid command selected.")
            return None

        # Ensure required keys are present (example keys)
        if not all(
            key in selected_command for key in ("path", "shell_type", "commands")
        ):
            print("Error: Selected command is missing required information.")
            return None

        return selected_command

    except Exception as e:
        print(f"Error executing command: {e}")
        return None


def create_process_status_table(
    processes: List[subprocess.Popen], process_names: List[str]
) -> Table:
    """
    Create a status table for running processes.

    Args:
        processes: List of running processes
        process_names: List of process names

    Returns:
        Rich Table object showing process status
    """
    table = Table(title="Process Status")
    table.add_column("Process Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("PID", style="blue")

    for process, name in zip(processes, process_names):
        status = "Running" if process.poll() is None else "Terminated"
        status_style = "green" if status == "Running" else "red"
        table.add_row(
            name, f"[{status_style}]{status}[/{status_style}]", str(process.pid)
        )

    return table


def main():
    """
    Main entry point for the Command Builder Application.

    This function handles:
    - Parsing command-line arguments to determine the mode of operation:
        - `-c` / `--create`: Create a new command list.
        - `-s` / `--start-server`: Start the server with existing commands.
        - `-e` / `--execute`: Execute commands immediately after creation.
        - `--config`: Specify a configuration file path (default: config.yaml).
    - Command list creation, if specified, using `create_new_command`.
    - Command execution using `execute_commands` to retrieve the command link and details.
    - Initializing and starting server processes based on the specified commands.
    - Monitoring the server processes, restarting if necessary, and handling unexpected terminations.
    - Launching separate threads for each process to stream their output in real-time.

    If the application is interrupted (Ctrl+C) or encounters an error, all processes are safely terminated using
    `kill_servers`.

    Raises:
        RuntimeError: If command creation or execution encounters an issue.
    """

    processes = []
    console = Console()
    try:

        # Argument parsing setup
        parser = argparse.ArgumentParser(
            description="Command Builder Application",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
            Examples:
            %(prog)s -c                 # Create a new command list
            %(prog)s -s                 # Start the server with existing commands
            %(prog)s -c -e             # Create and execute commands immediately
            """,
        )

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-c", "--create", action="store_true", help="Create a new command list"
        )
        group.add_argument(
            "-s",
            "--start-server",
            action="store_true",
            help="Start the server with existing commands",
        )

        parser.add_argument(
            "-e",
            "--execute",
            action="store_true",
            help="Execute commands immediately after creation",
        )

        parser.add_argument(
            "--config",
            type=str,
            default="config.yaml",
            help="Path to configuration file (default: config.yaml)",
        )

        args = parser.parse_args()
        # End of argument parsing setup.
        if args.execute and not args.create:
            parser.error("--execute can only be used with --create")

        # Handle command creation
        if args.create:
            try:
                create_new_command()
                if not args.execute:
                    sys.exit(
                        0
                    )  # Exit after creating a command list if not executing as well
            except Exception as e:
                console.print(f"\n[red] An error occured {e} [/red]")
                sys.exit(1)

        # Handle command execution
        if args.start_server or (args.create and args.execute):
            command_link = execute_commands()

        if not command_link or command_link == None:
            console.print(f"\n[red] No commands selected for execution. [/red]")
            sys.exit()

        path = command_link.get("path")
        shell_type = command_link.get("shell_type")
        commands_list = command_link.get("commands", [])

        # Ensure valid command list
        if not commands_list:
            console.print(
                "\n[red] No commands provided in command link. Exiting. [/red]"
            )
            sys.exit(1)

        # Initialize CommandRunner and set up servers
        process_runner = CommandRunner(path=path, shell_type=shell_type)
        processes, process_names = process_runner.setup_servers(commands_list)
        if not processes:
            console.print("\n [red] Failed to start any servers. Exiting. [/red]")
            sys.exit(1)
            # Start threads to read output from each process
        threads = []
        for process, name in zip(processes, process_names):
            t = threading.Thread(target=read_output, args=(process, name), daemon=True)
            t.start()
            threads.append(t)

        console.print("\n[info]Press Ctrl+C to stop all servers[/info]\n")

        # Main loop to monitor process status
        with Live(console=console, refresh_per_second=1) as live:
            while True:

                # Update process status table
                status_table = create_process_status_table(processes, process_names)
                live.update(status_table)

                # Check for terminated processes
                alive_processes = [p for p in processes if p.poll() is None]

                if not alive_processes:
                    console.print("[warning]All processes have terminated[/warning]")
                    break

                # Handle unexpected process termination
                dead_processes = [p for p in processes if p.poll() is not None]
                for p in dead_processes:
                    idx = processes.index(p)
                    console.print(
                        f"[warning]Process '{name}' terminated unexpectedly[/warning]"
                    )

                    # Remove the terminated process
                    processes.pop(idx)
                    process_names.pop(idx)

                time.sleep(1)  # Avoid busy waiting

    except KeyboardInterrupt:
        console.print("\n[yellow]Received shutdown signal[/yellow]")

    finally:
        kill_servers(processes)
        console.print("[success]All servers stopped successfully[/success]")


if __name__ == "__main__":
    main()
