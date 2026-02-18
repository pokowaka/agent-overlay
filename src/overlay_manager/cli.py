import argparse
import sys
import os
from .core import OverlayManager

def main():
    parser = argparse.ArgumentParser(description="AI Agent Workspace Overlay Manager")
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

    args = parser.parse_args()

    # Use a project-specific base if we can detect it, otherwise use current dir
    base = os.path.abspath(args.base if hasattr(args, 'base') else '.')
    manager = OverlayManager(base_dir=base)

    try:
        if args.command == "start":
            merged_path = manager.start_task(args.name)
            print(f"✅ Task '{args.name}' started.")
            print(f"📂 Mount point: {merged_path}")
            print(f"💡 Hint: {manager.get_bazel_hint(args.name)}")
        
        elif args.command == "abort":
            manager.abort_task(args.name)
            print(f"🛑 Task '{args.name}' aborted and cleaned up.")
        
        elif args.command == "diff":
            diff_output = manager.diff_task(args.name)
            print(diff_output)
        
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
