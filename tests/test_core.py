"""Unit tests for the OverlayManager core logic.

These tests verify the lifecycle of task overlays, including creation,
isolation, modification tracking (diff), and cleanup.
"""

import os
import pytest
import shutil
from overlay_manager.core import OverlayManager

@pytest.fixture
def base_dir(tmp_path):
    """Fixture to provide a temporary base directory with initial content."""
    d = tmp_path / "base"
    d.mkdir()
    (d / "file.txt").write_text("hello world")
    return str(d)

@pytest.fixture
def tasks_root(tmp_path):
    """Fixture to provide a temporary directory for task metadata."""
    d = tmp_path / "tasks"
    d.mkdir()
    return str(d)

@pytest.fixture
def manager(base_dir, tasks_root):
    """Fixture to provide an OverlayManager instance configured with temp paths."""
    return OverlayManager(base_dir=base_dir, tasks_root=tasks_root)

def test_task_lifecycle(manager, base_dir):
    """Tests the full lifecycle of a task: start -> modify -> diff -> list -> abort."""
    task_name = "test_task"
    
    # Start
    merged_path = manager.start_task(task_name)
    assert os.path.exists(merged_path)
    assert os.path.ismount(merged_path)
    
    # Modify
    test_file = os.path.join(merged_path, "file.txt")
    with open(test_file, "a") as f:
        f.write("\nnew line")
    
    # Verify base is unchanged (isolation)
    with open(os.path.join(base_dir, "file.txt"), "r") as f:
        assert f.read() == "hello world"
    
    # Diff (track modifications)
    diff = manager.diff_task(task_name)
    assert "new line" in diff
    
    # List (active tasks)
    assert task_name in manager.list_tasks()
    
    # Abort (cleanup)
    manager.abort_task(task_name)
    assert not os.path.exists(merged_path)
    assert task_name not in manager.list_tasks()

def test_start_duplicate_task(manager):
    """Tests that starting a task with a duplicate name raises a ValueError."""
    task_name = "dup_task"
    manager.start_task(task_name)
    with pytest.raises(ValueError, match="already exists"):
        manager.start_task(task_name)
    manager.abort_task(task_name)

def test_abort_nonexistent_task(manager):
    """Tests that aborting a task that doesn't exist raises a ValueError."""
    with pytest.raises(ValueError, match="not found"):
        manager.abort_task("ghost")
