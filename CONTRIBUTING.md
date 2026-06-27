# Contributing to Rectury

Thanks for your interest in contributing to Rectury.

Rectury is still in an early stage, so small and focused improvements are
welcome. You can contribute by fixing bugs, improving documentation, adding
tools, improving the terminal interface, or suggesting new ideas.

## Getting Started

Fork the repository and clone your fork:

```bash
git clone https://github.com/YOUR-USERNAME/Rectury-Desktop.git
cd Rectury-Desktop
```

Create a virtual environment and install the dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

Copy the example environment file if you want to run Rectury:

```bash
cp .env.example .env
```

Never commit your `.env` file or API keys.

## Creating a Branch

Create a separate branch for your change:

```bash
git checkout -b feature/short-description
```

Use a clear branch name, for example:

```text
feature/add-read-file-tool
fix/conversation-loading
docs/improve-setup-guide
```

## Making Changes

Try to keep each contribution focused on one problem.

- Write simple and readable Python.
- Use four spaces for indentation.
- Choose names that explain what the code does.
- Avoid adding dependencies unless they are necessary.
- Do not mix unrelated changes in the same Pull Request.
- Update the documentation when behavior changes.

## Adding a Tool

A Rectury tool normally requires these changes:

1. Add the Python function inside `tools/functions/`.
2. Create `tools/<tool_name>/prompt.py` with the model-facing prompt/schema.
3. Create `tools/<tool_name>/tool.py` pointing at the implementation.
4. Add the package to `tools/manifest.py`.

Tools must return data that can be converted to JSON.

Keep tools explicit and predictable. Destructive or sensitive actions should
not run without clear user confirmation.

## Checking Your Changes

Run the same syntax check used by GitHub Actions:

```bash
python -m compileall -q agent.py core tools ui
```

You should also run Rectury manually when your change affects the interface,
conversation flow, model client, or tools:

```bash
python3 agent.py
```

Do not include local conversations from `~/.rectury/`, secrets, temporary
files, or virtual environments in your commit.

## Committing

Use a short commit message that describes the change:

```bash
git add .
git commit -m "Add read file tool"
```

## Opening a Pull Request

Push your branch and open a Pull Request against `main`:

```bash
git push origin feature/short-description
```

In the Pull Request, explain:

- What changed.
- Why the change is useful.
- How you tested it.
- Any limitations or unfinished work.

GitHub Actions must pass before the Pull Request is merged.

## Reporting Bugs

Use the [GitHub issue tracker](https://github.com/Rectury-AI/Rectury-Desktop/issues)
for normal bugs and feature requests.

When reporting a bug, include:

- What you expected to happen.
- What actually happened.
- Steps to reproduce the problem.
- Your operating system and Python version.
- Relevant error messages without API keys or personal information.

Do not open a public issue for a security vulnerability. Follow the
[security policy](SECURITY.md) instead.

## Questions and Ideas

For larger features or architectural changes, open an issue before writing a
large amount of code. This helps confirm the direction and avoids duplicated
work.
