# Rectury

Rectury is an open-source, terminal-first personal computer agent. It connects a language model to a controlled Python tool system so users can ask for work in natural language, see the assistant reason and respond in real time, and gradually automate local computer tasks through explicit tools.

Rectury is not designed to be just another coding agent. The long-term goal is to become a general-purpose Personal Computer Agent capable of understanding, operating, and automating tasks across the entire computer.

Rectury is currently early-stage. The focus is the core agent loop: streaming responses, tool calling, tool execution, and a clean Textual-based terminal interface.

## Why Rectury

Most AI assistants can explain how to do something, but they do not operate your computer through a clear, inspectable tool layer. Rectury is built around a simple idea:

```text
User request -> Model -> Tool call -> Local tool -> Tool result -> Model response
```

The long-term goal is not just chat. Rectury is intended to become a local-first computer agent that can help with files, applications, browser workflows, development tasks, and repeatable personal automation while keeping the user in control.

## Long-Term Vision

Rectury is being built as a Personal Computer Agent.

The goal is to move beyond chat and enable users to operate their computers through natural language.

Future capabilities may include:

- File management
- Application control
- Browser automation
- Development workflows
- Communication tools
- Local automation
- Task planning and execution

## Core Principles

Rectury is built around a few core ideas:

- Local-first whenever possible
- Transparent tool execution
- User-controlled permissions
- Extensible architecture
- Provider independence
- Open source by default

## Current Features

- Textual terminal interface
- Streaming assistant responses
- OpenAI-compatible client configured for xAI
- Tool schemas loaded from JSON
- Tool dispatch through a Python registry
- Local `.env` configuration
- Extensible `tools/functions` structure
- MIT licensed

## Model Providers

Rectury currently uses xAI models through an OpenAI-compatible API.

Planned providers:

- xAI (current)
- OpenAI
- Anthropic
- Google Gemini
- Local models (Ollama)

The long-term goal is provider independence, allowing users to choose their preferred model.

## Current Tooling

Rectury currently includes a growing collection of local tools. The initial focus is filesystem operations and agent infrastructure.

Tools are defined in three places:

- `tools/schemas.json`: exposes the tool schema to the model.
- `tools/registry.py`: maps tool names to Python functions.
- `tools/functions/`: contains the actual tool implementations.

Current example:

- `list_files_in_dir`: lists files in a given directory.

## Current Development Stage

Rectury is currently focused on building the agent foundation:

- Streaming responses
- Tool calling
- Tool execution
- Tool registry
- Terminal UI

Desktop automation, browser control, and advanced workflows are planned for future releases.

## Requirements

- Python 3.10+
- An xAI API key

## Installation

```bash
git clone https://github.com/your-username/rectury.git
cd Rectury-Desktop
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Configuration

Create a local environment file:

```bash
cp .env.example .env
```

Add your API key:

```env
XAI_API_KEY=your_api_key_here
```

## Usage

```bash
python3 agent.py
```

## Project Structure

```text
core/
  chat.py             Agent loop and streaming/tool handling
  client.py           xAI/OpenAI-compatible client setup
  tool_runner.py      Tool dispatch logic

tools/
  schemas.json        Tool definitions visible to the model
  registry.py         Python tool registry
  functions/          Tool implementations

ui/
  terminal.py         Textual chat interface
  theme.py            Terminal styling

agent.py              Application entry point
```

## Safety Direction

Rectury should keep the model separate from direct system control. The model can request a tool, but local Python code decides what actually runs.

Planned safety principles:

- explicit tool schemas
- local execution boundaries
- clear error reporting
- permission prompts for sensitive actions
- no hidden background actions
- no destructive actions without confirmation

## Roadmap

- Add more filesystem tools: read, search, copy, move, and create files
- Add structured tool result formats
- Add permission prompts for risky operations
- Improve multi-step tool loops
- Add local session history
- Add richer tool status messages in the UI
- Experiment with desktop and browser automation

## Status

Rectury is experimental and under active development. APIs, tool formats, and internal structure may change as the agent loop becomes more capable.

## Contributing

Contributions are welcome.

If you'd like to help:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

Early feedback, bug reports, and architecture suggestions are also appreciated.

## License

Rectury is released under the MIT License. See [LICENSE](LICENSE) for details.
