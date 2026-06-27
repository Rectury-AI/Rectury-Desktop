from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SessionState:
    workspace: Path
    read_files: dict[str, str] = field(default_factory=dict)
    todos: list[dict] = field(default_factory=list)
    checkpoints: list[dict] = field(default_factory=list)
    reference_paths: list[str] = field(default_factory=list)
    shell_cwd: str | None = None
    shell_env: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_cwd(cls):
        return cls(workspace=Path.cwd().resolve())

    def remember_file(self, file_path, content_hash):
        self.read_files[str(file_path)] = content_hash

    def get_file_hash(self, file_path):
        return self.read_files.get(str(file_path))

    def forget_file(self, file_path):
        self.read_files.pop(str(file_path), None)

    def set_todos(self, todos):
        self.todos = todos

    def get_todos(self):
        return list(self.todos)

    def set_checkpoints(self, checkpoints):
        self.checkpoints = checkpoints

    def add_checkpoint(self, checkpoint):
        self.checkpoints.append(checkpoint)

    def get_checkpoints(self):
        return list(self.checkpoints)

    def pop_checkpoint(self):
        if not self.checkpoints:
            return None

        return self.checkpoints.pop()

    def set_reference_paths(self, reference_paths):
        self.reference_paths = list(reference_paths or [])

    def get_reference_paths(self):
        return list(self.reference_paths)

    def add_reference_path(self, reference_path):
        value = str(reference_path)

        if value not in self.reference_paths:
            self.reference_paths.append(value)

        return value

    def remove_reference_path(self, reference_path):
        value = str(reference_path)

        if value in self.reference_paths:
            self.reference_paths.remove(value)
            return value

        return None

    def get_shell_cwd(self):
        return self.shell_cwd or str(self.workspace)

    def set_shell_cwd(self, path):
        self.shell_cwd = str(path)

    def get_shell_env(self):
        return dict(self.shell_env)

    def set_shell_env(self, key, value):
        self.shell_env[str(key)] = str(value)

    def unset_shell_env(self, key):
        self.shell_env.pop(str(key), None)
