import subprocess
import time
import os
import signal
import selectors
import shlex
from uuid import uuid4
from pathlib import Path

from core.command_security import validate_command
from core.workspace import resolve_workspace_path


def run_command(command, state, cwd=".", timeout=30):
    final_result = None

    for event in run_command_stream(command, state, cwd=cwd, timeout=timeout):
        if event.get("type") == "result":
            final_result = event["result"]

    return final_result or {"error": "command produced no result."}


def run_command_stream(
    command,
    state,
    cwd=".",
    timeout=30,
    cancel_event=None,
    on_process=None,
):
    validation = validate_command(command)

    if not validation["ok"]:
        yield {
            "type": "result",
            "result": {
                "error": validation["error"],
                "code": validation.get("code", "invalid_command"),
            },
        }
        return

    if not isinstance(timeout, int) or timeout < 1:
        timeout = 30

    timeout = min(timeout, 120)

    if isinstance(cwd, str) and cwd.lower() == "none":
        cwd = None

    cd_result = handle_persistent_shell_builtin(command, state, cwd)

    if cd_result is not None:
        yield {"type": "result", "result": cd_result}
        return

    if cwd is None:
        workdir = None
    elif cwd == "." and hasattr(state, "get_shell_cwd"):
        try:
            workdir = resolve_workspace_path(state.workspace, state.get_shell_cwd())
        except Exception as e:
            yield {"type": "result", "result": {"error": str(e)}}
            return
    else:
        try:
            workdir = resolve_workspace_path(state.workspace, cwd)
        except Exception as e:
            yield {"type": "result", "result": {"error": str(e)}}
            return

        if not workdir.exists():
            yield {
                "type": "result",
                "result": {"error": f"cwd does not exist: {workdir}"},
            }
            return

    started_at = time.monotonic()
    stdout_parts = []
    stderr_parts = []
    selector = selectors.DefaultSelector()
    process = None
    cwd_marker = f"__RECTURY_CWD_{uuid4().hex}__"
    wrapped_command = (
        f"{command}\n"
        "__rectury_status=$?\n"
        f"printf '\\n{cwd_marker}%s\\n' \"$PWD\"\n"
        "exit $__rectury_status"
    )
    env = os.environ.copy()

    if hasattr(state, "get_shell_env"):
        env.update(state.get_shell_env())

    try:
        process = subprocess.Popen(
            wrapped_command,
            shell=True,
            cwd=workdir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )

        if on_process is not None:
            on_process(process)

        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")

        timed_out = False
        cancelled = False

        while selector.get_map():
            if cancel_event is not None and cancel_event.is_set():
                cancelled = True
                terminate_process(process)

            if time.monotonic() - started_at > timeout:
                timed_out = True
                terminate_process(process)

            for key, _ in selector.select(timeout=0.1):
                chunk = key.fileobj.readline()

                if chunk:
                    parsed_cwd = parse_cwd_marker(chunk, cwd_marker)
                    if parsed_cwd is not None:
                        update_shell_cwd(state, parsed_cwd)
                        continue

                    stream_name = key.data

                    if stream_name == "stdout":
                        stdout_parts.append(chunk)
                    else:
                        stderr_parts.append(chunk)

                    yield {
                        "type": "output",
                        "stream": stream_name,
                        "content": chunk,
                        "duration_ms": int(
                            (time.monotonic() - started_at) * 1000
                        ),
                    }
                else:
                    selector.unregister(key.fileobj)

            if process.poll() is not None:
                for pipe, stream_name in (
                    (process.stdout, "stdout"),
                    (process.stderr, "stderr"),
                ):
                    remaining = pipe.read() if pipe else ""

                    if remaining:
                        remaining, parsed_cwd = strip_cwd_marker(
                            remaining,
                            cwd_marker,
                        )
                        if parsed_cwd is not None:
                            update_shell_cwd(state, parsed_cwd)

                    if remaining:
                        if stream_name == "stdout":
                            stdout_parts.append(remaining)
                        else:
                            stderr_parts.append(remaining)

                        yield {
                            "type": "output",
                            "stream": stream_name,
                            "content": remaining,
                            "duration_ms": int(
                                (time.monotonic() - started_at) * 1000
                            ),
                        }

                break

        returncode = process.wait()
    except Exception as e:
        yield {"type": "result", "result": {"error": str(e)}}
        return
    finally:
        try:
            selector.close()
        except Exception:
            pass

    duration_ms = int((time.monotonic() - started_at) * 1000)
    stdout = "".join(stdout_parts)
    stderr = "".join(stderr_parts)

    if timed_out:
        yield {
            "type": "result",
            "result": {
                "error": f"command timed out after {timeout}s",
                "code": "timeout",
                "command": command,
                "cwd": str(workdir) if workdir is not None else None,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": duration_ms,
                "safe": validation["safe"],
                "prefix": validation.get("prefix", ""),
            },
        }
        return

    if cancelled:
        yield {
            "type": "result",
            "result": {
                "error": "command cancelled by user",
                "code": "cancelled",
                "command": command,
                "cwd": str(workdir) if workdir is not None else None,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "duration_ms": duration_ms,
                "safe": validation["safe"],
                "prefix": validation.get("prefix", ""),
            },
        }
        return

    yield {
        "type": "result",
        "result": {
            "success": returncode == 0,
            "command": command,
            "cwd": str(workdir) if workdir is not None else None,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "safe": validation["safe"],
            "prefix": validation.get("prefix", ""),
        },
    }


def handle_persistent_shell_builtin(command, state, cwd):
    try:
        parts = shlex.split(command)
    except ValueError:
        return None

    if not parts:
        return None

    if parts[0] == "cd":
        return handle_persistent_cd_parts(command, parts, state, cwd)

    if parts[0] == "export":
        return handle_persistent_export(command, parts, state)

    if parts[0] == "unset":
        return handle_persistent_unset(command, parts, state)

    return None


def handle_persistent_cd_parts(command, parts, state, cwd):
    if len(parts) > 2:
        return None

    target = parts[1] if len(parts) == 2 else "."
    base = (
        Path(state.get_shell_cwd())
        if cwd in {None, "."} and hasattr(state, "get_shell_cwd")
        else resolve_workspace_path(state.workspace, cwd or ".")
    )
    requested = Path(target).expanduser()

    if not requested.is_absolute():
        requested = base / requested

    try:
        next_cwd = resolve_workspace_path(state.workspace, requested)
    except ValueError as error:
        return {"error": str(error), "code": "invalid_cwd"}

    if not next_cwd.exists():
        return {"error": f"cwd does not exist: {next_cwd}", "code": "invalid_cwd"}

    if not next_cwd.is_dir():
        return {"error": f"cwd is not a directory: {next_cwd}", "code": "invalid_cwd"}

    if hasattr(state, "set_shell_cwd"):
        state.set_shell_cwd(next_cwd)

    return {
        "success": True,
        "command": command,
        "cwd": str(next_cwd),
        "returncode": 0,
        "stdout": str(next_cwd) + "\n",
        "stderr": "",
        "duration_ms": 0,
        "safe": False,
        "prefix": "cd",
        "shell_cwd_updated": True,
    }


def handle_persistent_export(command, parts, state):
    if not hasattr(state, "set_shell_env"):
        return None

    if len(parts) == 1:
        env = state.get_shell_env() if hasattr(state, "get_shell_env") else {}
        output = "\n".join(f"export {key}={value}" for key, value in sorted(env.items()))
        return {
            "success": True,
            "command": command,
            "cwd": state.get_shell_cwd() if hasattr(state, "get_shell_cwd") else None,
            "returncode": 0,
            "stdout": output + ("\n" if output else ""),
            "stderr": "",
            "duration_ms": 0,
            "safe": False,
            "prefix": "export",
            "shell_env_updated": False,
        }

    updated = {}

    for assignment in parts[1:]:
        if "=" not in assignment:
            return None

        key, value = assignment.split("=", 1)

        if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
            return None

        state.set_shell_env(key, value)
        updated[key] = value

    return {
        "success": True,
        "command": command,
        "cwd": state.get_shell_cwd() if hasattr(state, "get_shell_cwd") else None,
        "returncode": 0,
        "stdout": "\n".join(f"{key}={value}" for key, value in updated.items()) + "\n",
        "stderr": "",
        "duration_ms": 0,
        "safe": False,
        "prefix": "export",
        "shell_env_updated": True,
        "env_keys": sorted(updated),
    }


def handle_persistent_unset(command, parts, state):
    if not hasattr(state, "unset_shell_env") or len(parts) < 2:
        return None

    removed = []

    for key in parts[1:]:
        if not key or not key.replace("_", "").isalnum() or key[0].isdigit():
            return None

        state.unset_shell_env(key)
        removed.append(key)

    return {
        "success": True,
        "command": command,
        "cwd": state.get_shell_cwd() if hasattr(state, "get_shell_cwd") else None,
        "returncode": 0,
        "stdout": "\n".join(removed) + "\n",
        "stderr": "",
        "duration_ms": 0,
        "safe": False,
        "prefix": "unset",
        "shell_env_updated": True,
        "env_keys": sorted(removed),
    }


def parse_cwd_marker(text, marker):
    stripped = str(text).strip()

    if not stripped.startswith(marker):
        return None

    return stripped[len(marker):]


def strip_cwd_marker(text, marker):
    lines = str(text).splitlines(keepends=True)
    kept = []
    cwd = None

    for line in lines:
        parsed = parse_cwd_marker(line, marker)

        if parsed is None:
            kept.append(line)
        else:
            cwd = parsed

    return "".join(kept), cwd


def update_shell_cwd(state, cwd):
    if not cwd or not hasattr(state, "set_shell_cwd"):
        return

    path = Path(cwd).expanduser()

    if path.exists() and path.is_dir():
        state.set_shell_cwd(path.resolve())


def terminate_process(process):
    if process.poll() is not None:
        return

    try:
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()
    except Exception:
        process.terminate()
