# Product Management Document: Copy-on-Write (COW) FUSE Overlay for Gemini CLI

## 1. Overview
The **Gemini CLI Agent Overlay** is a proposed system to enable multiple `gemini-cli` agents to operate concurrently on the same codebase without interfering with each other's file modifications. By utilizing a Copy-on-Write (COW) FUSE file overlay, each agent is isolated within its own "transactional view" of the project.

## 2. Problem Statement
Currently, `gemini-cli` is limited by the "single-agent-per-directory" constraint. When an agent modifies a file (e.g., fixing a bug), any other agent started in the same directory will see those partial, uncommitted changes. This prevents disjoint tasks (e.g., refactoring A while fixing bug B) from progressing in parallel. Traditional solutions like multiple git checkouts are heavy on disk space and configuration time.

## 3. Target Users
*   **Power Developers:** Who want to delegate multiple independent tasks to agents simultaneously.
*   **CI/CD Orchestrators:** Running parallel validation or automated repair agents.
*   **Experimentalists:** Users who want to test a major refactor without risk to their primary workspace.

## 4. Proposed Solution: COW FUSE Overlay
The solution leverages Linux `fuse-overlayfs` (or similar technology) to create ephemeral, per-agent directory views.

### 4.1. Core Concepts
*   **Base Directory (Lower):** The original, read-only view of the source code.
*   **Task Overlay (Upper/COW):** A private, writable directory where an agent's changes are stored.
*   **Transaction:** A lifecycle comprising the creation, operation, and resolution (commit/abort) of an overlay.

## 5. Key Workflows

### 5.1. Starting a Transaction
A user initiates a task with a unique name:
`gemini task start --name "fix-auth-bug"`
This command:
1.  Creates a temporary `upperdir` in `~/.gemini/tasks/fix-auth-bug/`.
2.  Mounts a FUSE overlay at a new mount point (e.g., `~/work/project_fix-auth-bug`).
3.  Initializes a new `gemini-cli` instance scoped to this mount point.

### 5.2. Independent Execution
The agent performs edits, runs tests, and interacts with the filesystem within the isolated mount point. Changes are invisible to the Base Directory and other active tasks.

### 5.3. Completion & Resolution
Once the task is complete, the user can choose:
*   **Commit:** Merge the changes from the `upperdir` back into the Base Directory.
*   **Abort (Recommended):** Unmount the overlay. Since the workflow is primarily `repo`/`git` based, the user can capture the `diff` between the `upperdir` and `lowerdir` as a patch, apply it to the main branch via git, and discard the overlay.

## 6. Use Cases

### 6.1. Simultaneous Bug Fix and Feature Work
*   **User Scenario:** A developer is working on a new UI feature. Suddenly, a P0 bug is reported in the backend.
*   **Action:** The user starts a second agent in a COW overlay to fix the P0 bug while the first agent continues the UI work in the main directory.
*   **Benefit:** Zero context switching for the user; both tasks progress in parallel.

### 6.2. Parallel "What-If" Explorations
*   **User Scenario:** An agent is asked to "evaluate three different libraries for JSON parsing."
*   **Action:** Three agents are spawned in three separate overlays, each implementing a different library.
*   **Benefit:** High-speed comparison without polluting the main branch with three sets of temporary changes.

### 6.3. Concurrent Testing of a Refactor
*   **User Scenario:** A large-scale refactor is being performed by an agent.
*   **Action:** While the refactor is in progress, another agent runs intensive integration tests in a separate overlay to catch regressions early.

## 7. Functional Requirements
*   **Isolation:** Files modified in one overlay must not be visible in another.
*   **Transparency:** The agent must not know it is running in an overlay; standard tools (`ls`, `grep`, `blaze`) must work as expected.
*   **Performance:** The overhead of the FUSE filesystem should not significantly slow down build times.
*   **Persistence:** Task overlays should survive shell restarts until explicitly aborted.

## 8. Technical Challenges & Mitigations
*   **Build Cache Invalidation:** Overlaying files might confuse build tools (like `blaze`) that rely on mtimes or inodes.
    *   *Mitigation:* Use overlay-aware caching or separate build artifact directories per task.
*   **Disk Space:** Many large overlays could consume disk.
    *   *Mitigation:* Periodically clean up abandoned task directories.
*   **Kernel Dependencies:** `fuse-overlayfs` requires specific kernel support.
    *   *Mitigation:* Provide a fallback to simple directory copies or Docker-based isolation if FUSE is unavailable.

## 9. Future Considerations
*   **Merging Conflict Resolution:** Tools to help a user merge two disjoint sets of COW changes that accidentally touched the same file.
*   **Integration with `repo`:** Automatic mapping of COW transactions to `repo start` branches.
