# Command Runner

Command Runner is a local script execution environment designed to allow users to build, execute, and monitor custom scripts and command lists. It maintains logs and status information for each run, enabling streamlined management of multiple processes in parallel.

## Overview
Command Runner provides a CLI-based tool that helps developers execute scripts or commands locally, track their status, and manage process lifecycles. It is particularly useful for running multiple scripts simultaneously, ensuring that each process runs in a controlled environment with real-time output streaming, error handling, and automated cleanup.

## Key Features
* Script Execution and Management: Easily create, execute, and manage lists of commands.
* Real-time Output and Status Monitoring: Stream real-time output for each process and display a dynamic status table.
* Process Lifecycle Management: Automatically handle process terminations and resource cleanup.
* Process Logging: Logs return codes and process information, capturing details for debugging and tracking.
* Graceful Shutdown: Interrupts are handled to ensure all processes terminate safely, preventing orphaned child processes.
## Requirements
**Python 3.6** or higher
Modules: `subprocess, threading, time, psutil, argparse, rich, typing`
**Install dependencies** (if needed):

bash```
pip install psutil rich```
## Installation
*Clone the repository:*

```bash
git clone https://github.com/your-username/command-runner.git
cd command-runner
```
*Run the setup:*

```bash
python main.py --help
```
- Usage
- Basic Commands
The CLI interface provides several options for creating and managing command lists and servers.

## Create a Command List:

bash```
python main.py -c```
This command opens an interactive mode to create a list of commands.

## Start Servers with Existing Commands:

bash```
Copy code
python main.py -s```
## Create and Immediately Execute a Command List:

bash```
python main.py -c -e```
Examples
bash```
python main.py -c                 # Create a new command list
python main.py -s                 # Start the server with existing commands
python main.py -c -e              # Create and execute commands immediately```
## Code Structure
CommandBuilder: Builds and validates command lists, saving them for reuse.
CommandViewer: Provides an interactive viewer for navigating and selecting commands.
CommandRunner: Manages command execution, handling process initiation and cleanup.
## Helper Functions:
* read_output: Streams process output in real-time.
* kill_process_tree: Terminates a process and its children recursively.
* kill_servers: Stops all active processes, ensuring proper cleanup.
* create_process_status_table: Creates a table to monitor process statuses.
## Process Management and Cleanup
Command Runner handles process terminations gracefully:

## Interrupt Handling: KeyboardInterrupt signals safely terminate all processes.
Child Process Cleanup: Orphaned processes are avoided by terminating all child processes recursively.
Example Workflow
Start by creating a command list:
bash```
python main.py -c```
Once saved, start the servers with:

bash```
python main.py -s ```
## Contributing
We welcome contributions! If you’d like to improve or add features, please fork the repository, create a new branch, and submit a pull request.

This README provides clear guidance on the functionality and usage of the Command Runner tool, giving potential users a complete picture of what it can achieve and how to get started. Let me know if you want further customization or additional sections!
