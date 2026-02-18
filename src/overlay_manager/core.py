"""Core logic for managing Copy-on-Write (COW) FUSE overlays.

This module provides the OverlayManager class which orchestrates the creation,
management, and destruction of isolated workspace views using fuse-overlayfs.
"""

import os
import subprocess
import shutil
from pathlib import Path

class OverlayManager:
    """Manages the lifecycle of agent workspace overlays.
    
    Attributes:
        base_dir: The absolute path to the base (read-only) directory.
        tasks_root: The absolute path to the directory where task data is stored.
    """

    def __init__(self, base_dir: str, tasks_root: str = None):
        """Initializes the OverlayManager.
        
        Args:
            base_dir: The directory to be used as the lower (read-only) layer.
            tasks_root: Optional custom directory for task metadata and upper layers.
                       Defaults to ~/.agent_tasks.
        """
        self.base_dir = os.path.abspath(base_dir)
        if tasks_root:
            self.tasks_root = os.path.abspath(tasks_root)
        else:
            self.tasks_root = os.path.join(os.path.expanduser("~"), ".agent_tasks")
        
        os.makedirs(self.tasks_root, exist_ok=True)

    def _get_task_paths(self, task_name: str) -> dict:
        """Generates the filesystem paths for a specific task.
        
        Args:
            task_name: The unique identifier for the task.
            
        Returns:
            A dictionary containing paths for 'root', 'upper', 'work', and 'merged'.
        """
        task_dir = os.path.join(self.tasks_root, task_name)
        return {
            "root": task_dir,
            "upper": os.path.join(task_dir, "upper"),
            "work": os.path.join(task_dir, "work"),
            "merged": os.path.join(task_dir, "merged"),
        }

    def check_prerequisites(self):
        """Checks if the necessary system tools and modules are available.
        
        Raises:
            RuntimeError: If fuse-overlayfs or /dev/fuse is missing.
        """
        # Check for fuse-overlayfs binary
        if shutil.which("fuse-overlayfs") is None:
            raise RuntimeError(
                "'fuse-overlayfs' not found. It is required for rootless overlay support.\n"
                "Installation: sudo apt install fuse-overlayfs"
            )

        # Check for /dev/fuse
        if not os.path.exists("/dev/fuse"):
            raise RuntimeError(
                "/dev/fuse not found. The FUSE kernel module must be loaded.\n"
                "Try running: sudo modprobe fuse"
            )

    def start_task(self, task_name: str) -> str:
        """Starts a new task by mounting a COW overlay.
        
        Args:
            task_name: The unique name for the new task.
            
        Returns:
            The absolute path to the merged (writable) view.
            
        Raises:
            ValueError: If a task with the same name already exists.
            RuntimeError: If fuse-overlayfs is missing or the mount fails.
        """
        self.check_prerequisites()
        paths = self._get_task_paths(task_name)
        
        if os.path.exists(paths["root"]):
            raise ValueError(f"Task '{task_name}' already exists at {paths['root']}")

        os.makedirs(paths["upper"])
        os.makedirs(paths["work"])
        os.makedirs(paths["merged"])

        # fuse-overlayfs -o lowerdir=LOW,upperdir=UP,workdir=WORK MERGED
        cmd = [
            "fuse-overlayfs",
            "-o", f"lowerdir={self.base_dir},upperdir={paths['upper']},workdir={paths['work']}",
            paths["merged"]
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return paths["merged"]
        except subprocess.CalledProcessError as e:
            shutil.rmtree(paths["root"])
            raise RuntimeError(f"Failed to mount overlay: {e.stderr}")

    def abort_task(self, task_name: str) -> bool:
        """Stops and cleans up a task overlay.
        
        Args:
            task_name: The name of the task to abort.
            
        Returns:
            True if successful.
            
        Raises:
            ValueError: If the task does not exist.
        """
        paths = self._get_task_paths(task_name)
        
        if not os.path.exists(paths["root"]):
            raise ValueError(f"Task '{task_name}' not found.")

        # Unmount
        if os.path.exists(paths["merged"]) and os.path.ismount(paths["merged"]):
            try:
                subprocess.run(["fusermount", "-u", paths["merged"]], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                # If it fails, maybe it's lazy unmount?
                subprocess.run(["fusermount", "-uz", paths["merged"]], check=True)

        # Cleanup
        shutil.rmtree(paths["root"])
        return True

    def list_tasks(self) -> list:
        """Lists all active task names.
        
        Returns:
            A list of task name strings.
        """
        if not os.path.exists(self.tasks_root):
            return []
        return os.listdir(self.tasks_root)

    def diff_task(self, task_name: str) -> str:
        """Generates a recursive diff of changes made in the task.
        
        Args:
            task_name: The name of the task to diff.
            
        Returns:
            A string containing the diff output.
            
        Raises:
            ValueError: If the task does not exist.
        """
        paths = self._get_task_paths(task_name)
        if not os.path.exists(paths["root"]):
            raise ValueError(f"Task '{task_name}' not found.")

        cmd = ["diff", "-Nur", self.base_dir, paths["merged"]]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    def get_bazel_hint(self, task_name: str) -> str:
        """Generates a recommended Bazel command for isolated builds.
        
        Args:
            task_name: The name of the task.
            
        Returns:
            A string containing the recommended build command.
        """
        paths = self._get_task_paths(task_name)
        output_base = os.path.join(paths["root"], "bazel_out")
        return f"bazel --output_base={output_base} build //..."
