import argparse
import os
import subprocess
import sys
from pathlib import Path


__version__ = "0.3.0"
REQUIRED_RUNTIME_MODULES = ("textual", "openai", "dotenv", "PIL")


def repo_root():
    return Path(__file__).resolve().parent


def repo_venv():
    return repo_root() / ".venv"


def repo_venv_python():
    if os.name == "nt":
        return repo_venv() / "Scripts" / "python.exe"
    return repo_venv() / "bin" / "python"


def running_from_repo_venv():
    try:
        return Path(sys.prefix).resolve() == repo_venv().resolve()
    except OSError:
        return False


def missing_runtime_modules():
    missing = []

    for module in REQUIRED_RUNTIME_MODULES:
        try:
            __import__(module)
        except ModuleNotFoundError:
            missing.append(module)

    return missing


def install_requirements(python_executable):
    requirements = repo_root() / "requirements.txt"
    try:
        subprocess.check_call(
            [str(python_executable), "-m", "pip", "install", "-r", str(requirements)]
        )
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            "rectury: could not install Python dependencies automatically.\n\n"
            "Run this once manually:\n"
            f"  {python_executable} -m pip install -r {requirements}"
        ) from error


def create_repo_venv():
    venv = repo_venv()
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
    except subprocess.CalledProcessError as error:
        raise SystemExit(
            "rectury: could not create the local Python environment.\n\n"
            "Run this once manually:\n"
            f"  python3 -m venv {venv}"
        ) from error


def ensure_source_runtime():
    missing = missing_runtime_modules()
    if not missing:
        return

    venv_python = repo_venv_python()
    if not running_from_repo_venv():
        if not venv_python.exists():
            print("Setting up Rectury local Python environment...")
            create_repo_venv()
            install_requirements(venv_python)

        os.execv(
            str(venv_python),
            [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]],
        )

    print("Installing Rectury Python dependencies...")
    install_requirements(sys.executable)

    missing = missing_runtime_modules()
    if not missing:
        return

    modules = ", ".join(missing)
    raise SystemExit(
        "rectury: missing Python dependencies: "
        f"{modules}\n\n"
        "Try again after installing dependencies with:\n"
        f"  {sys.executable} -m pip install -r {repo_root() / 'requirements.txt'}\n\n"
        "Then run again:\n"
        "  python3 agent.py"
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="rectury",
        description="Start Rectury in the selected workspace.",
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default=".",
        help="Workspace directory to open. Defaults to the current directory.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"rectury {__version__}",
    )
    return parser


def resolve_workspace(value):
    workspace = Path(value).expanduser().resolve()

    if not workspace.exists():
        raise SystemExit(f"rectury: workspace does not exist: {workspace}")

    if not workspace.is_dir():
        raise SystemExit(f"rectury: workspace is not a directory: {workspace}")

    return workspace


def create_app():
    ensure_source_runtime()

    from ui.terminal import RecturyApp

    return RecturyApp(ansi_color=True)


def main(argv=None):
    args = build_parser().parse_args(argv)
    workspace = resolve_workspace(args.workspace)
    os.chdir(workspace)
    ensure_source_runtime()
    create_app().run()


if __name__ == "__main__":
    main()
