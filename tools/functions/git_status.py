import subprocess

from core.workspace import resolve_workspace_path


def run_git(args, cwd, timeout=10):
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"error": "git is not installed.", "code": "git_missing"}
    except subprocess.TimeoutExpired:
        return {"error": "git command timed out.", "code": "timeout"}

    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def git_status(state, path="."):
    try:
        workdir = resolve_workspace_path(state.workspace, path)
    except ValueError as error:
        return {"error": str(error), "code": "invalid_path"}

    root_result = run_git(["rev-parse", "--show-toplevel"], workdir)

    if root_result.get("error"):
        return root_result

    if root_result["returncode"] != 0:
        return {
            "error": "workspace is not inside a git repository.",
            "code": "not_git_repo",
            "stderr": root_result.get("stderr", ""),
        }

    repo_root = root_result["stdout"].strip()
    branch = run_git(["branch", "--show-current"], repo_root)
    status = run_git(["status", "--short", "--branch"], repo_root)
    diff_stat = run_git(["diff", "--stat"], repo_root)
    staged_diff_stat = run_git(["diff", "--cached", "--stat"], repo_root)
    last_commit = run_git(["log", "-1", "--oneline"], repo_root)

    return {
        "success": True,
        "repo_root": repo_root,
        "branch": branch.get("stdout", "").strip(),
        "status": status.get("stdout", ""),
        "diff_stat": diff_stat.get("stdout", ""),
        "staged_diff_stat": staged_diff_stat.get("stdout", ""),
        "last_commit": last_commit.get("stdout", "").strip(),
        "errors": {
            "branch": branch.get("stderr", "").strip(),
            "status": status.get("stderr", "").strip(),
            "diff_stat": diff_stat.get("stderr", "").strip(),
            "staged_diff_stat": staged_diff_stat.get("stderr", "").strip(),
            "last_commit": last_commit.get("stderr", "").strip(),
        },
    }
