import os
import subprocess
import shutil
from pathlib import Path

class OverlayManager:
    def __init__(self, base_dir: str, tasks_root: str = None):
        self.base_dir = os.path.abspath(base_dir)
        if tasks_root:
            self.tasks_root = os.path.abspath(tasks_root)
        else:
            self.tasks_root = os.path.join(os.path.expanduser("~"), ".agent_tasks")
        
        os.makedirs(self.tasks_root, exist_ok=True)

    def _get_task_paths(self, task_name: str):
        task_dir = os.path.join(self.tasks_root, task_name)
        return {
            "root": task_dir,
            "upper": os.path.join(task_dir, "upper"),
            "work": os.path.join(task_dir, "work"),
            "merged": os.path.join(task_dir, "merged"),
        }

    def start_task(self, task_name: str):
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
        except FileNotFoundError:
            shutil.rmtree(paths["root"])
            raise RuntimeError("'fuse-overlayfs' not found. Please install it with: sudo apt install fuse-overlayfs")
        except subprocess.CalledProcessError as e:
            shutil.rmtree(paths["root"])
            raise RuntimeError(f"Failed to mount overlay: {e.stderr}")

    def abort_task(self, task_name: str):
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

    def list_tasks(self):
        if not os.path.exists(self.tasks_root):
            return []
        return os.listdir(self.tasks_root)

    def diff_task(self, task_name: str):
        paths = self._get_task_paths(task_name)
        if not os.path.exists(paths["root"]):
            raise ValueError(f"Task '{task_name}' not found.")

        cmd = ["diff", "-Nur", self.base_dir, paths["merged"]]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout

    def get_bazel_hint(self, task_name: str):
        paths = self._get_task_paths(task_name)
        output_base = os.path.join(paths["root"], "bazel_out")
        return f"blaze --output_base={output_base} build //..."
