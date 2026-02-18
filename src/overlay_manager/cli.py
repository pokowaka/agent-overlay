"""Command-line interface for the AI Agent Workspace Overlay Manager.

This module provides the entry point for the 'agent-overlay' tool,
mapping CLI commands to the underlying OverlayManager logic.
"""

import argparse
import sys
import os
from .core import OverlayManager

def main():
    """Entry point for the agent-overlay CLI.
    
    Parses arguments and executes the corresponding OverlayManager methods.
    Exits with code 1 on error.
    """
    parser = argparse.ArgumentParser(
        description="""
AI Agent Workspace Overlay Manager.

This tool creates isolated, writable workspace views using Copy-on-Write (COW) FUSE overlays. 
It allows multiple AI agents (or humans) to work concurrently on the same codebase without 
interfering with each other or the base repository.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Workflow:
  1. Start a new task isolation:
     $ agent-overlay start my-bug-fix --base /path/to/repo

  2. Navigate to the isolated mount point (provided in 'start' output):
     $ cd ~/.agent_tasks/my-bug-fix/merged

  3. Run your AI agent or make manual changes:
     $ gemini-cli "Fix the bug in src/main.py"

  4. Run tests in isolation (using the recommended hint):
     $ bazel --output_base=~/.agent_tasks/my-bug-fix/bazel_out build //...

  5. Review your changes from the original repo directory:
     $ agent-overlay diff my-bug-fix

  6. Apply changes to your main branch (via git) and cleanup:
     $ agent-overlay abort my-bug-fix
"""
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Start command
    start_p = subparsers.add_parser("start", help="Start a new task overlay")
    start_p.add_argument("name", help="Task name")
    start_p.add_argument("--base", default=".", help="Base directory (default: current)")

    # Abort command
    abort_p = subparsers.add_parser("abort", help="Abort and cleanup a task overlay")
    abort_p.add_argument("name", help="Task name")

    # Diff command
    diff_p = subparsers.add_parser("diff", help="Show changes made in the task overlay")
    diff_p.add_argument("name", help="Task name")

    # List command
    list_p = subparsers.add_parser("list", help="List active task overlays")

    # Shell command
    shell_p = subparsers.add_parser("shell", help="Enter an isolated shell for a task")
    shell_p.add_argument("name", help="Task name")

    args = parser.parse_args()

    # Use a project-specific base if we can detect it, otherwise use current dir
    base = os.path.abspath(args.base if hasattr(args, 'base') else '.')
    manager = OverlayManager(base_dir=base)

    try:
        if args.command == "start":
            merged_path = manager.start_task(args.name)
            print(f"✅ Task '{args.name}' started.")
            print(f"📂 Mount point: {merged_path}")
            print(f"🚀 To enter the isolated view, run:")
            print(f"   ./agent-overlay shell {args.name}")
            print(f"💡 Hint: {manager.get_bazel_hint(args.name)}")
        
        elif args.command == "abort":
            manager.abort_task(args.name)
            print(f"🛑 Task '{args.name}' aborted and cleaned up.")
        
        elif args.command == "diff":
            diff_output = manager.diff_task(args.name)
            print(diff_output)
        
        elif args.command == "shell":
            manager.enter_shell(args.name)
        
        elif args.command == "list":
            tasks = manager.list_tasks()
            if not tasks:
                print("No active tasks.")
            else:
                print("Active Tasks:")
                for t in tasks:
                    print(f" - {t}")
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
