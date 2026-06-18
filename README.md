# Rectury

**Talk to your computer from the terminal.**

Rectury is an open-source personal computer agent that connects a language
model to a controlled set of local tools. Ask for something in natural
language, watch the response stream in real time, and let the agent use
explicit tools when the task requires action.

> Rectury is experimental and under active development. Its APIs and internal
> structure may change while the core agent becomes more capable.

## See It in Action

### Start a Conversation

Rectury provides a clean, keyboard-first interface built with Textual.

![Rectury chat interface responding to a greeting](docs/images/rectury-chat-demo.png)

## What Works Today

- Interactive terminal interface
- Streaming assistant responses
- Multi-step tool calls
- OpenAI-compatible model providers
- JSON tool schemas and a Python tool registry
- Extensible tool implementations
- Local environment configuration
- Local conversation history with generated titles

The first available tool, `list_files_in_dir`, lets Rectury inspect the
contents of a directory. More filesystem and computer-control tools are
planned.

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Rectury-AI/Rectury-Desktop.git
cd Rectury-Desktop
```

### 2. Create the Environment

Rectury requires Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows, activate the environment with:

```powershell
.venv\Scripts\activate
```

### 3. Configure a Model

Copy the example configuration:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
AI_PROVIDER=openai
AI_MODEL=your-model-name
AI_API_KEY=your-api-key
AI_BASE_URL=https://api.openai.com/v1
```

Rectury works with providers that expose an OpenAI-compatible API, including
OpenAI, OpenRouter, xAI, and local Ollama models.

For Ollama, a configuration can look like this:

```env
AI_PROVIDER=ollama
AI_MODEL=qwen3
AI_API_KEY=ollama
AI_BASE_URL=http://localhost:11434/v1
```

### 4. Run Rectury

```bash
python3 agent.py
```

## Project Structure

```text
Rectury-Desktop/
├── agent.py                 Application entry point
├── core/
│   ├── chat.py              Agent loop, streaming, and tool calls
│   ├── client.py            Model provider configuration
│   ├── conversation_store.py Local JSON conversation storage
│   └── tool_runner.py       Local tool dispatch
├── tools/
│   ├── functions/           Tool implementations
│   ├── registry.py
│   └── schemas.json
├── ui/
│   ├── components.py
│   ├── terminal.py          Textual interface
│   └── theme.py
└── docs/images/             README screenshots
```

## Where Rectury Is Going

The goal is broader than chat: Rectury is being built toward a local-first
agent that can help operate and automate a personal computer.

Conversations are stored as JSON files in `~/.rectury/conversations/`. Rectury
automatically resumes the most recently updated conversation when it starts.

Planned areas include:

- More filesystem tools for reading, searching, creating, copying, and moving
  files
- Permission prompts for sensitive actions
- Structured tool results and clearer execution status
- Conversation browsing and creating new sessions from the interface
- Desktop and browser automation
- Repeatable multi-step workflows

## Safety Direction

Rectury is designed around an explicit boundary between the model and the
system. The model proposes tool calls; trusted local code validates and
executes them.

The project is moving toward:

- Clear permission prompts for risky operations
- No hidden background actions
- No destructive actions without confirmation
- Useful errors when a tool cannot run
- Local execution boundaries that remain easy to inspect

Only run Rectury inside projects and directories you trust.

## How Tools Work

The model does not access your system directly. It requests a defined tool,
local Python code executes it, and the result is returned to the conversation.

![Rectury using a tool to inspect files in the current workspace](docs/images/rectury-tool-use-demo.png)

```text
You ask -> Model chooses a tool -> Rectury runs it -> Model responds
```

Adding a tool currently involves three small pieces:

```text
tools/
├── schemas.json       Describes tools to the model
├── registry.py        Connects tool names to Python functions
└── functions/         Contains the implementations
```

This separation keeps tool execution inspectable: the model can request an
action, but local code remains responsible for what actually runs.

## Contributing

Rectury is early, so focused contributions can have a meaningful impact.
Bug reports, architecture discussions, new tools, and UI improvements are
welcome

1. Fork the repository.
2. Create a feature branch.
3. Make and test your changes.
4. Open a pull request explaining what changed and why.

## License

Rectury is available under the [MIT License](LICENSE).
