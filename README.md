# Agent Workspace Overlay

A Copy-on-Write (COW) FUSE overlay manager to enable multiple AI agents (e.g., Gemini CLI, Claude Code, etc.) to work concurrently on the same codebase without interference.

## Prerequisites
- **Linux Kernel:** Support for FUSE and User Namespaces.
- **fuse-overlayfs:** The FUSE implementation of overlayfs.
  - Install with: `sudo apt install fuse-overlayfs`
- **FUSE Module:** Ensure the `fuse` module is loaded.
  - Check with: `lsmod | grep fuse`
  - Load with: `sudo modprobe fuse`

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
This creates an isolated, writable view of your repository at `~/.agent_tasks/my-fix/merged/`.

### 2. Work in the Isolated View
The easiest way to work is to enter an isolated shell:
```bash
./agent-overlay shell my-fix
```
This automatically takes you into the merged directory in a new sub-shell. You can run any agent or tools here without affecting the base repo. Type `exit` to return.

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
- **Build Systems (Bazel):** The tool recommends using a unique `--output_base` for each task to avoid build cache conflicts.

## Testing
Run tests with:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python3 -m pytest
```
