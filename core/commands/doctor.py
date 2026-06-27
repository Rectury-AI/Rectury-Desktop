import os
import sys
import platform
from pathlib import Path


def check_environment() -> list:
    """Check environment configuration"""
    checks = []

    # Check API provider
    provider = os.getenv("AI_PROVIDER", "").strip()
    if provider:
        checks.append(f"[ok] AI_PROVIDER: {provider}")
    else:
        checks.append("[missing] AI_PROVIDER: Not set")

    # Check API key
    api_key = os.getenv("AI_API_KEY", "").strip()
    if api_key:
        checks.append("[ok] AI_API_KEY: Set")
    else:
        checks.append("[missing] AI_API_KEY: Not set")

    # Check model
    model = os.getenv("AI_MODEL", "").strip()
    if model:
        checks.append(f"[ok] AI_MODEL: {model}")
    else:
        checks.append("[missing] AI_MODEL: Not set")

    # Check base URL
    base_url = os.getenv("AI_BASE_URL", "").strip()
    if base_url:
        checks.append(f"[ok] AI_BASE_URL: {base_url}")
    else:
        checks.append("[missing] AI_BASE_URL: Not set")

    return checks


def check_system() -> list:
    """Check system information"""
    checks = []

    checks.append(f"[ok] Python: {platform.python_version()}")
    checks.append(f"[ok] Platform: {platform.platform()}")
    checks.append(f"[ok] System: {platform.system()} {platform.release()}")

    # Check if running in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        checks.append("[ok] Virtual Environment: Active")
    else:
        checks.append("[warn] Virtual Environment: Not detected")

    return checks


def check_directories() -> list:
    """Check required directories"""
    checks = []

    home = Path.home()
    rectury_dir = home / ".rectury"

    if rectury_dir.exists():
        checks.append(f"[ok] Config directory: {rectury_dir}")
    else:
        checks.append(f"[warn] Config directory: {rectury_dir} (will be created)")

    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        checks.append("[ok] .env file: Found")
    else:
        checks.append("[warn] .env file: Not found in current directory")

    return checks


def check_dependencies() -> list:
    """Check Python dependencies"""
    checks = []

    required_packages = [
        "openai",
        "textual",
        "python-dotenv",
    ]

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            checks.append(f"[ok] {package}: Installed")
        except ImportError:
            checks.append(f"[missing] {package}: Not installed")

    return checks


def run_diagnostics() -> str:
    """Run a full diagnostic check."""
    output = ["Rectury Doctor - System Diagnostics\n"]

    output.append("Environment Configuration:")
    output.extend(check_environment())
    output.append("")

    output.append("System Information:")
    output.extend(check_system())
    output.append("")

    output.append("Directories:")
    output.extend(check_directories())
    output.append("")

    output.append("Dependencies:")
    output.extend(check_dependencies())
    output.append("")

    output.append("Diagnostics complete.")

    return "\n".join(output)


def handle_doctor_command() -> str:
    """Handle /doctor command"""
    return run_diagnostics()
