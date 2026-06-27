import os

from core.context import IGNORED_DIRS
from core.workspace import resolve_workspace_path


MAX_RECURSIVE_FILES = 1000


def is_ignored(path):
    return any(part in IGNORED_DIRS for part in path.parts)


def recursive_files(path, workspace):
    results = []

    for root, dirs, files in os.walk(path):
        root_path = resolve_workspace_path(workspace, root)
        dirs[:] = sorted(
            directory
            for directory in dirs
            if not is_ignored((root_path / directory).relative_to(workspace))
        )

        for file_name in sorted(files):
            file_path = root_path / file_name

            try:
                relative_path = file_path.relative_to(workspace)
            except ValueError:
                continue

            if is_ignored(relative_path):
                continue

            results.append(str(relative_path))

            if len(results) >= MAX_RECURSIVE_FILES:
                return results, True

    return results, False


def tree_from_paths(paths):
    tree = {}

    for path in paths:
        current = tree
        for part in path.split(os.sep):
            current = current.setdefault(part, {})

    def render(node, prefix=""):
        lines = []
        items = sorted(node.items())

        for index, (name, children) in enumerate(items):
            connector = "`-- " if index == len(items) - 1 else "|-- "
            lines.append(f"{prefix}{connector}{name}")

            if children:
                extension = "    " if index == len(items) - 1 else "|   "
                lines.extend(render(children, prefix + extension))

        return lines

    return "\n".join(render(tree))


def list_files_in_dir(directory, state, recursive=False):
    try:
        path = resolve_workspace_path(state.workspace, directory)
        if recursive:
            files, truncated = recursive_files(path, state.workspace)
            tree = tree_from_paths(files)
            return {
                "success": True,
                "directory": str(path),
                "files": files,
                "tree": tree,
                "truncated": truncated,
            }

        files = sorted(os.listdir(path))
        return {
            "success": True,
            "directory": str(path),
            "files": files,
        }
    except Exception as e:
        return {"error": str(e)}
