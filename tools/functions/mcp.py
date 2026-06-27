import json
import os
import select
import subprocess
import time
from pathlib import Path

from core.workspace import resolve_workspace_path


CONFIG_PATH = ".rectury/mcp.json"
PROTOCOL_VERSION = "2024-11-05"


def mcp_config_path(state):
    return state.workspace / CONFIG_PATH


def load_mcp_config(state):
    path = mcp_config_path(state)

    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.get("servers", data)

    if not isinstance(servers, dict):
        raise ValueError("MCP config must contain a servers object.")

    return servers


def redact_server(server):
    visible = {
        key: value
        for key, value in server.items()
        if key not in {"env", "headers", "token", "apiKey", "api_key"}
    }
    env = server.get("env")

    if isinstance(env, dict):
        visible["env"] = {
            key: "***" if any(secret in key.lower() for secret in ("key", "token", "secret"))
            else value
            for key, value in env.items()
        }

    return visible


def mcp_list_servers(state):
    try:
        servers = load_mcp_config(state)
    except Exception as error:
        return {"error": str(error)}

    return {
        "success": True,
        "config_path": str(mcp_config_path(state)),
        "servers": [
            {"name": name, **redact_server(server)}
            for name, server in sorted(servers.items())
            if isinstance(server, dict)
        ],
        "total": len(servers),
    }


def encode_message(message):
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def read_exact(stream, length, deadline):
    chunks = []
    remaining = length

    while remaining > 0:
        timeout = deadline - time.monotonic()

        if timeout <= 0:
            raise TimeoutError("MCP server timed out.")

        readable, _, _ = select.select([stream], [], [], timeout)

        if not readable:
            raise TimeoutError("MCP server timed out.")

        chunk = stream.read(remaining)

        if not chunk:
            raise EOFError("MCP server closed stdout.")

        chunks.append(chunk)
        remaining -= len(chunk)

    return b"".join(chunks)


def read_message(stream, deadline):
    headers = {}

    while True:
        timeout = deadline - time.monotonic()

        if timeout <= 0:
            raise TimeoutError("MCP server timed out.")

        readable, _, _ = select.select([stream], [], [], timeout)

        if not readable:
            raise TimeoutError("MCP server timed out.")

        line = stream.readline()

        if not line:
            raise EOFError("MCP server closed stdout.")

        line = line.decode("ascii", errors="replace").strip()

        if not line:
            break

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        headers[key.lower()] = value.strip()

    length = int(headers.get("content-length", "0"))

    if length <= 0:
        raise ValueError("MCP server returned a frame without Content-Length.")

    return json.loads(read_exact(stream, length, deadline).decode("utf-8"))


def write_message(process, message):
    process.stdin.write(encode_message(message))
    process.stdin.flush()


def server_command(state, name):
    servers = load_mcp_config(state)
    server = servers.get(name)

    if not isinstance(server, dict):
        raise ValueError(f"MCP server not found: {name}")

    command = server.get("command")

    if not isinstance(command, str) or not command:
        raise ValueError(f"MCP server {name} is missing command.")

    args = server.get("args", [])

    if not isinstance(args, list):
        raise ValueError(f"MCP server {name} args must be a list.")

    cwd = server.get("cwd")
    workdir = resolve_workspace_path(state.workspace, cwd) if cwd else state.workspace
    env = os.environ.copy()

    if isinstance(server.get("env"), dict):
        env.update({str(key): str(value) for key, value in server["env"].items()})

    return [command, *[str(arg) for arg in args]], workdir, env


def run_mcp_request(state, server_name, method, params=None, timeout=15):
    try:
        timeout = max(1, min(int(timeout), 60))
    except (TypeError, ValueError):
        timeout = 15

    deadline = time.monotonic() + timeout
    command, workdir, env = server_command(state, server_name)
    process = subprocess.Popen(
        command,
        cwd=workdir,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        write_message(
            process,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "rectury", "version": "0.3.0"},
                },
            },
        )
        initialize = read_message(process.stdout, deadline)

        if initialize.get("error"):
            return {"error": initialize["error"], "code": "mcp_initialize_failed"}

        write_message(
            process,
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        write_message(
            process,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": params or {},
            },
        )
        response = read_message(process.stdout, deadline)

        if response.get("error"):
            return {"error": response["error"], "code": "mcp_request_failed"}

        return {
            "success": True,
            "server": server_name,
            "method": method,
            "result": response.get("result"),
        }
    except Exception as error:
        stderr = ""

        try:
            stderr = process.stderr.read().decode("utf-8", errors="replace")
        except Exception:
            pass

        return {
            "error": str(error),
            "code": "mcp_error",
            "stderr": stderr[-2000:],
        }
    finally:
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass


def mcp_list_tools(server, state, timeout=15):
    if not isinstance(server, str) or not server.strip():
        return {"error": "server must be a non-empty string."}

    return run_mcp_request(state, server.strip(), "tools/list", {}, timeout)


def mcp_call_tool(server, tool, arguments=None, state=None, timeout=30):
    if not isinstance(server, str) or not server.strip():
        return {"error": "server must be a non-empty string."}

    if not isinstance(tool, str) or not tool.strip():
        return {"error": "tool must be a non-empty string."}

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return {"error": "arguments must be an object."}

    return run_mcp_request(
        state,
        server.strip(),
        "tools/call",
        {"name": tool.strip(), "arguments": arguments},
        timeout,
    )
