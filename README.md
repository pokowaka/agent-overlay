# Agent Workspace Overlay

A Copy-on-Write (COW) FUSE overlay manager to enable multiple AI agents (e.g., Gemini CLI, Claude Code, etc.) to work concurrently on the same codebase without interference.

## Prerequisites
- Linux
- `fuse-overlayfs` (Install with: `sudo apt install fuse-overlayfs`)

## Installation
You can install the project in editable mode for development:
```bash
pip install -e .
```

## Usage
The `agent-overlay` script provides the primary interface.

### 1. Start a New Task
```bash
./agent-overlay start my-fix --base /path/to/your/repo
```
This creates an isolated, writable view of your repository at `~/.gemini/tasks/my-fix/merged/`. (Note: The task root remains under `~/.gemini/tasks` for now as a default, but can be configured).

### 2. Work in the Isolated View
Change directory to the task's merged view and run your agents there:
```bash
cd ~/.gemini/tasks/my-fix/merged/
# Run any agent here
```

### 3. Review Changes
To see what the agent has modified:
```bash
./agent-overlay diff my-fix
```

### 4. Abort and Cleanup
When the task is complete (or you've applied the changes via git), cleanup the overlay:
```bash
./agent-overlay abort my-fix
```

### 5. List Active Tasks
```bash
./agent-overlay list
```

## How it Works
- **Lower Directory:** Your original repository (read-only).
- **Upper Directory:** A private directory where all modifications are stored.
- **Merged View:** A FUSE mount combining the two, giving you a full, writable view of the repository while keeping the original safe.
- **Build Systems (Bazel/Blaze):** The tool recommends using a unique `--output_base` for each task to avoid build cache conflicts.

## Testing
Run tests with:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python3 -m pytest
```
