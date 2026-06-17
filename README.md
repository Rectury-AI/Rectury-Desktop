# Rectury — Project Blueprint

> **Rectury is an open-source Personal Computer Agent that can understand requests in natural language, operate a computer through tools, automate multi-step tasks, and keep the user in control through explicit permissions and visible execution.**

---

## 1. Project overview

Rectury is not intended to be only a chatbot, a coding assistant, or a terminal wrapper around an LLM.

The objective is to build a **general-purpose Personal Computer Agent** that lives in the terminal and can understand what the user wants, decide which actions are required, execute those actions through a controlled tool system, verify the result, and report what happened.

A user should eventually be able to write requests such as:

```text
Open Steam and search for Cyberpunk 2077.
```

```text
Find the latest invoice in Downloads and move it to Documents/Invoices.
```

```text
Send Jan a message saying the build is ready.
```

```text
Open this project in VS Code, run the tests, and explain the errors.
```

```text
Search for a product, compare the available options, and prepare the purchase for my approval.
```

Rectury should interpret the request, build a plan, use the required tools, ask for confirmation when an action is sensitive, execute the approved steps, verify the outcome, and show the process in real time.

---

## 2. The problem Rectury solves

Modern computers still require users to manually operate applications, navigate interfaces, manage files, search menus, repeat workflows, and move information between unrelated programs.

Existing AI assistants can often explain how to perform a task, but they do not always execute it reliably on the user's computer.

Existing coding agents are powerful inside software projects, but they are usually focused on:

- source code;
- terminals;
- repositories;
- tests;
- software development workflows.

Rectury aims to operate across the whole computer:

- files and folders;
- applications;
- the operating system;
- the browser;
- communication platforms;
- media;
- development tools;
- repetitive workflows;
- approved transactions.

The long-term objective is to reduce the distance between **what the user wants** and **what the computer does**.

---

## 3. Product definition

Rectury can be described as:

> **An open-source, terminal-first Personal Computer Agent that can understand, control, and automate a computer through natural language.**

Alternative descriptions:

> **An AI agent for operating your computer, not just talking about it.**

> **A terminal-first agent that connects language models to real computer actions.**

> **An open-source computer operator with tools, permissions, memory, and visible execution.**

The preferred product category is:

```text
Personal Computer Agent
```

Other valid category names are:

```text
Desktop Agent
Computer-Use Agent
AI Computer Agent
General-Purpose Desktop Agent
```

Rectury should not be presented primarily as an AI coding agent because programming is only one part of its intended scope.

---

## 4. Core vision

The final vision is:

```text
Natural-language request
        ↓
Intent understanding
        ↓
Task planning
        ↓
Tool selection
        ↓
Permission check
        ↓
Action execution
        ↓
Result verification
        ↓
Clear user report
```

Rectury should eventually be capable of:

1. Understanding broad user goals.
2. Breaking complex tasks into smaller steps.
3. Choosing the appropriate tools.
4. Operating across several applications.
5. Tracking the current state of a task.
6. Recovering from errors.
7. Asking the user when information or approval is required.
8. Remembering useful project and user context.
9. Showing every important action.
10. Reversing actions when technically possible.

---

## 5. What makes Rectury different

Rectury should not compete only on being open source. Other open-source agents already exist.

Its differentiation should come from the combination of the following principles.

### 5.1 General computer operation

Rectury is designed to operate the whole computer, not only code repositories.

Its scope includes:

```text
Code
Files
Applications
Browser
Messages
System controls
Media
Automation
Personal workflows
```

### 5.2 Terminal-first experience

Rectury uses the terminal as its main interface because the terminal is:

- fast;
- universal;
- familiar to developers and technical users;
- easy to automate;
- suitable for logs and visible actions;
- compatible with remote systems;
- lightweight compared with a full desktop application.

The terminal interface should still be visually polished through Textual or Rich.

### 5.3 Visible execution

Rectury should never appear to act invisibly.

The user should see states such as:

```text
Thinking…
Planning task…
Opening Steam…
Searching for Cyberpunk 2077…
Waiting for confirmation…
Action completed.
```

### 5.4 Permission-first design

Rectury should distinguish between observing, modifying, communicating, purchasing, and destructive actions.

The agent must not treat all tools equally.

### 5.5 Local-first control

Where possible:

- configuration should be stored locally;
- memory should be stored locally;
- session history should be stored locally;
- the user should control which model provider is used;
- the user should control which tools are enabled;
- the user should be able to use their own API key.

### 5.6 Extensible tool system

Rectury should be designed so new tools can be added without rewriting the entire agent.

The long-term goal is a tool/plugin ecosystem.

### 5.7 General agent plus specialist capabilities

Rectury should remain general-purpose while offering strong specialist modules for:

- file management;
- browser automation;
- software development;
- communication;
- desktop control;
- personal workflows.

### 5.8 Action verification

A tool returning without raising an error does not always mean the task succeeded.

Rectury should verify important actions.

Examples:

- after opening an application, confirm that its process or window exists;
- after moving a file, confirm the destination exists;
- after creating a folder, confirm it was created;
- after sending a message, confirm the platform reports success;
- after editing code, run tests or inspect the diff;
- after preparing a purchase, re-check the final price.

---

## 6. What Rectury is not

Rectury is not intended to be:

- only a chatbot;
- only a coding agent;
- only a voice assistant;
- a hidden background automation system;
- an unrestricted shell executor;
- an autonomous buyer;
- an agent that sends messages without review;
- an agent that bypasses platform rules;
- a replacement for user judgment in sensitive decisions.

Rectury should assist and execute, but the user remains responsible for high-impact decisions.

---

## 7. Target users

### Initial users

The first versions should target:

- developers;
- technical students;
- open-source users;
- power users;
- people comfortable with terminals;
- people interested in automation.

These users are more tolerant of early technical limitations and can provide useful feedback.

### Later users

Once reliability and usability improve:

- creators;
- founders;
- office workers;
- researchers;
- small teams;
- non-technical users through simplified commands or a graphical layer.

---

## 8. Main use cases

### 8.1 File management

```text
Find all PDFs downloaded this month and move them into a new folder.
```

```text
Rename these screenshots using their creation date.
```

```text
Find duplicate files but do not delete anything.
```

### 8.2 Application control

```text
Open Spotify.
```

```text
Close Steam.
```

```text
Open this folder in Visual Studio Code.
```

### 8.3 Browser tasks

```text
Open GitHub and go to the Rectury repository.
```

```text
Search for train tickets and show me the best options.
```

```text
Fill in this form but do not submit it.
```

### 8.4 Communication

```text
Create a draft email to Jan explaining the current progress.
```

```text
Send this message after I approve it.
```

### 8.5 Software development

```text
Read this project and explain its architecture.
```

```text
Run the tests and identify the failures.
```

```text
Apply the fix, show me the diff, and ask before saving.
```

### 8.6 Media and system control

```text
Play my focus playlist.
```

```text
Set the volume to 30%.
```

```text
Tell me which applications are currently using the most memory.
```

### 8.7 Multi-step workflows

```text
Find the latest release build, upload it to the release page, and prepare the announcement text.
```

```text
Open the invoice, extract the amount, rename it, and move it to the correct month folder.
```

---

## 9. Core product principles

Rectury should follow these principles from the beginning.

### Principle 1: The model does not directly control the computer

The LLM decides which tool to request.

Rectury validates and executes the tool.

```text
LLM requests action
        ↓
Rectury validates arguments
        ↓
Rectury checks permissions
        ↓
Rectury executes local code
```

### Principle 2: Tools must be explicit

Each capability should have a clear name, parameters, return value, and risk level.

Bad:

```text
do_anything(command)
```

Better:

```text
open_application(name)
list_files(path)
read_file(path)
move_file(source, destination)
```

### Principle 3: Sensitive actions require confirmation

Sending, deleting, purchasing, publishing, uploading, and changing security settings require explicit approval.

### Principle 4: Every task must be interruptible

The user must always have a way to stop the agent.

### Principle 5: Errors must be understandable

Rectury should explain:

- what failed;
- which tool failed;
- why it may have failed;
- what it will try next;
- whether anything was modified.

### Principle 6: The UI must show real state

The interface should not invent progress messages unrelated to actual events.

### Principle 7: Start narrow, expand safely

A smaller set of reliable tools is more valuable than many unreliable tools.

---

## 10. Current technical direction

The initial implementation uses:

- **Python** for the agent runtime and tools;
- **Textual** for the terminal interface;
- **Rich** for formatted terminal output where useful;
- **xAI/Grok** as the initial model provider;
- **OpenAI-compatible Python SDK** for the xAI API;
- **JSON tool schemas** to describe tools to the model;
- **environment variables** for secrets;
- **GitHub** for source control and collaboration.

This stack may evolve, but the agent core should not be tightly coupled to one model provider.

---

## 11. High-level architecture

```text
┌─────────────────────────────────────────────┐
│              Terminal Interface             │
│       Input, output, streaming, status       │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│                 Agent Loop                  │
│  Message → Model → Tool call → Tool result  │
└───────────────┬─────────────────┬───────────┘
                │                 │
┌───────────────▼────────┐ ┌──────▼──────────┐
│     Model Provider     │ │  Tool Registry   │
│ Grok / future models   │ │ schemas + code   │
└────────────────────────┘ └──────┬──────────┘
                                  │
                         ┌────────▼──────────┐
                         │ Permission Layer  │
                         │ validation/risk   │
                         └────────┬──────────┘
                                  │
                         ┌────────▼──────────┐
                         │ Operating System  │
                         │ files/apps/web/UI │
                         └───────────────────┘
```

---

## 12. The agent loop

The agent loop is the core of Rectury.

A complete cycle should work as follows:

1. Receive the user's request.
2. Add it to the current session.
3. Build the context for the model.
4. Send the request and available tool schemas to the model.
5. Stream visible text when the model produces text.
6. Detect whether the model requested a tool.
7. Validate the tool name and arguments.
8. Check the tool's permission level.
9. Request user confirmation if necessary.
10. Execute the tool.
11. Collect its result.
12. Add the result to the conversation.
13. Call the model again.
14. Continue until the model returns a final answer or the step limit is reached.

```text
User request
    ↓
Model response
    ↓
Tool requested?
 ┌──┴──┐
 No   Yes
 │     ↓
 │  Validate
 │     ↓
 │  Permission
 │     ↓
 │  Execute
 │     ↓
 │  Return result
 │     ↓
 └── Model again
        ↓
   Final response
```

---

## 13. Streaming

Streaming is used so the response appears progressively instead of waiting for the full answer.

### Model streaming

The model can emit partial text events:

```text
"Opening"
" Steam"
" now"
"..."
```

Rectury displays them as they arrive.

### Tool execution

Tools do not automatically use the model's streaming mechanism.

A tool normally executes and returns one structured result.

For long-running tools, Rectury can emit its own progress events:

```text
tool_started
tool_progress
tool_finished
tool_failed
```

Example:

```text
● Searching files…
  500 files scanned
  1,000 files scanned
✓ 14 matching files found
```

### UI responsiveness

Model requests and slow tools must run outside the main Textual UI event loop, using workers or asynchronous tasks.

The interface must remain responsive while:

- the model is generating;
- a tool is executing;
- a browser page is loading;
- a command is running.

---

## 14. Tool system

Every tool has two parts.

### 14.1 Tool schema

The schema is what the model sees.

It defines:

- tool name;
- description;
- input parameters;
- required arguments;
- argument types.

Example concept:

```json
{
  "type": "function",
  "name": "open_application",
  "description": "Open an installed desktop application.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Application name"
      }
    },
    "required": ["name"]
  }
}
```

### 14.2 Tool implementation

The implementation is normal Python code that performs the real action.

```text
Model requests open_application("Steam")
        ↓
Rectury locates the Python function
        ↓
Permission system validates the action
        ↓
Python opens Steam
        ↓
Tool returns a structured result
```

### Recommended tool result format

Each tool should eventually return information similar to:

```json
{
  "success": true,
  "message": "Steam opened successfully.",
  "data": {},
  "error": null
}
```

A consistent result format makes the agent loop easier to maintain.

---

## 15. Tool categories

### 15.1 File system tools

Initial tools:

- `get_current_directory`
- `list_files`
- `read_file`
- `create_directory`
- `write_file`
- `copy_file`
- `move_file`
- `rename_file`
- `delete_file`
- `search_files`
- `search_text`

Important requirements:

- handle missing paths;
- reject invalid paths;
- detect binary files;
- limit file size;
- avoid accidental overwrite;
- use the recycle bin instead of permanent deletion where possible;
- return clear errors.

### 15.2 Application tools

- `open_application`
- `close_application`
- `list_running_applications`
- `get_active_window`
- `focus_window`

Important requirements:

- support platform-specific implementations;
- distinguish normal close from forced termination;
- verify whether the application opened;
- require approval for force-closing applications.

### 15.3 System tools

- `get_system_info`
- `get_disk_usage`
- `get_processes`
- `run_command`
- `get_clipboard`
- `set_clipboard`
- `set_volume`
- `mute_volume`

Important requirements:

- command timeout;
- command allow/block rules;
- safe working directory;
- structured stdout, stderr, and exit code;
- sensitive clipboard warnings;
- platform compatibility.

### 15.4 Visual desktop tools

- `take_screenshot`
- `click`
- `double_click`
- `type_text`
- `press_key`
- `scroll`
- `move_mouse`
- `find_text_on_screen`

Important requirements:

- prefer accessibility APIs over raw coordinates;
- use screenshots only when structured UI information is unavailable;
- display which screen or window is being controlled;
- provide an emergency stop;
- never type secrets automatically without direct approval.

### 15.5 Browser tools

- `browser_open`
- `browser_navigate`
- `browser_get_page`
- `browser_click`
- `browser_fill`
- `browser_select`
- `browser_download`
- `browser_upload`
- `browser_back`
- `browser_close`

Important requirements:

- prefer Playwright-style structured interaction over mouse coordinates;
- show the current URL;
- warn before submitting forms;
- confirm uploads;
- confirm external communication;
- block unsafe or deceptive navigation where possible.

### 15.6 Communication tools

- `create_email_draft`
- `send_email`
- `send_discord_message`
- `send_slack_message`
- `send_telegram_message`

Important requirements:

- show the final recipient;
- show the exact content;
- show attachments;
- require confirmation before sending;
- do not infer recipients when ambiguous;
- keep service credentials secure.

### 15.7 Development tools

- `git_status`
- `git_diff`
- `git_log`
- `run_tests`
- `read_file`
- `write_file`
- `apply_patch`
- `search_text`
- `run_command`

Important requirements:

- show diffs;
- protect uncommitted work;
- ask before destructive Git operations;
- never push automatically without explicit approval;
- run verification after modifications.

### 15.8 Media tools

- `play_media`
- `pause_media`
- `next_track`
- `previous_track`
- `set_volume`
- `mute_volume`

### 15.9 Commerce tools

Later-stage tools:

- `search_product`
- `compare_products`
- `add_to_cart`
- `prepare_purchase`
- `confirm_purchase`

Important requirements:

- never purchase based only on inferred intent;
- show total price;
- show taxes and fees;
- show seller;
- show subscription terms;
- show delivery information;
- require explicit final confirmation;
- never reveal payment credentials to the model.

### 15.10 Internal agent tools

- `ask_for_confirmation`
- `create_task_plan`
- `update_task_status`
- `save_memory`
- `search_memory`
- `undo_last_action`
- `report_error`

---

## 16. Recommended tool implementation order

### Stage 1: Read-only foundations

1. `get_current_directory`
2. `list_files`
3. `read_file`
4. `search_files`
5. `get_system_info`
6. `list_running_applications`

Goal:

> Rectury can observe the local environment without modifying it.

### Stage 2: Safe actions

7. `create_directory`
8. `open_application`
9. `open_url`
10. `set_clipboard`
11. `take_screenshot`

Goal:

> Rectury can perform small, visible, reversible actions.

### Stage 3: Controlled modifications

12. `write_file`
13. `copy_file`
14. `move_file`
15. `rename_file`
16. `run_command`

Goal:

> Rectury can complete useful workflows while using permission checks.

### Stage 4: Browser interaction

17. `browser_navigate`
18. `browser_get_page`
19. `browser_click`
20. `browser_fill`
21. `browser_download`

Goal:

> Rectury can complete structured web tasks.

### Stage 5: Visual desktop control

22. `get_active_window`
23. `focus_window`
24. `click`
25. `type_text`
26. `press_key`
27. `scroll`

Goal:

> Rectury can operate applications without direct APIs.

### Stage 6: Communication and sensitive actions

28. `create_email_draft`
29. `send_email`
30. platform-specific messaging tools
31. purchase preparation tools

Goal:

> Rectury can perform high-value actions under strict approval rules.

---

## 17. Permission and risk model

Every tool should have a risk classification.

### Level 0 — Observation

Normally automatic:

- list files;
- read files;
- inspect processes;
- inspect system information;
- view Git status;
- take a screenshot after user permission is configured.

### Level 1 — Low-risk action

May run automatically depending on user settings:

- open an application;
- open a URL;
- create a new empty folder;
- copy text to the clipboard.

### Level 2 — Modification

Should usually require confirmation or a trusted-session permission:

- write a file;
- rename a file;
- move a file;
- install a dependency;
- run a command;
- fill a form.

### Level 3 — External side effect

Always confirm:

- send a message;
- send an email;
- upload a file;
- submit a form;
- publish content;
- create an account;
- commit or push code.

### Level 4 — Destructive or financial

Always require explicit final confirmation:

- delete files;
- force-close applications;
- change security settings;
- execute administrator commands;
- purchase something;
- accept a subscription;
- make a payment;
- expose credentials.

Suggested confirmation UI:

```text
Rectury wants to send the following message:

To: Jan
Message: The latest build is ready.

[Approve once] [Edit] [Reject]
```

For purchases:

```text
Final purchase confirmation

Product: Cyberpunk 2077
Seller: Steam
Price: €29.99
Recurring payment: No
Payment method: Saved Steam payment method

[Confirm purchase] [Cancel]
```

---

## 18. Security requirements

Security must be part of the architecture, not an addition at the end.

### Secrets

- store API keys in `.env` or an operating-system credential store;
- never commit `.env`;
- provide `.env.example`;
- never print full secrets in logs;
- redact tokens and passwords from error reports.

### Commands

- use timeouts;
- capture exit codes;
- block obviously destructive commands;
- detect administrator elevation;
- restrict the working directory when relevant;
- ask for approval before installing software;
- show the exact command before execution.

### File access

- validate paths;
- detect attempts to escape an allowed workspace;
- warn before accessing sensitive folders;
- avoid permanent deletion;
- protect existing files from silent overwrite.

### Browser and messages

- confirm form submissions;
- confirm file uploads;
- confirm messages;
- display the destination domain;
- warn when authentication or financial details are involved.

### Logs

- do not store passwords;
- do not store API keys;
- allow the user to delete session history;
- clearly separate local logs from information sent to the model.

### Emergency stop

Rectury needs an immediate stop mechanism that:

- cancels the current model request;
- interrupts supported tools;
- stops keyboard and mouse automation;
- prevents the next planned action from starting.

---

## 19. Memory system

Sending the entire conversation on every request is simple but inefficient.

Rectury should eventually use several memory layers.

### 19.1 Recent conversation memory

Keep the most recent messages exactly as written.

Purpose:

- preserve immediate context;
- understand references such as “do that again”;
- maintain natural conversation.

### 19.2 Session summary

Compress older conversation turns into a structured summary.

Possible fields:

```text
Current objective
Completed actions
Important decisions
Files involved
Pending tasks
Errors encountered
User constraints
```

### 19.3 Task state

Keep structured runtime state, for example:

```json
{
  "task": "Open Steam and search for Cyberpunk 2077",
  "status": "waiting_for_confirmation",
  "completed_steps": [
    "Steam opened",
    "Product page found"
  ],
  "pending_steps": [
    "Add to cart"
  ]
}
```

### 19.4 Persistent memory

Store only information that remains useful over time:

- user-approved preferences;
- trusted applications;
- preferred browser;
- project instructions;
- recurring workflows;
- previous decisions.

### 19.5 Retrieval

Do not inject all saved memory into every model request.

Retrieve only relevant memories for the current task.

### 19.6 User control

The user should be able to:

- view saved memory;
- edit it;
- delete it;
- disable persistent memory;
- choose what categories may be stored.

---

## 20. Context management

The context sent to the model should eventually contain:

```text
System instructions
Current tool definitions
Relevant persistent memory
Current task state
Session summary
Recent messages
Latest tool results
Current user request
```

The context should not contain unnecessary logs or every file on the computer.

Rectury should use:

- recent-message windows;
- session summaries;
- selective memory retrieval;
- file relevance selection;
- tool result truncation;
- token limits;
- maximum agent steps.

---

## 21. User interface requirements

The terminal UI should make Rectury feel active, trustworthy, and understandable.

### Main UI elements

- Rectury logo or wordmark;
- current conversation;
- user input field;
- active model;
- current task status;
- active tool;
- permission prompts;
- error display;
- cancel/stop command;
- optional session information.

### Suggested states

```text
Idle
Thinking
Planning
Waiting for tool
Running tool
Waiting for permission
Streaming response
Completed
Failed
Cancelled
```

### Example execution

```text
You: Open Steam and search for Cyberpunk 2077.

◌ Planning…
● Opening Steam
✓ Steam opened
● Searching for Cyberpunk 2077
✓ Product page found

Rectury: I found the product page. Do you want me to open it?
```

### UI event model

The interface should respond to events such as:

```text
model_started
text_delta
tool_requested
permission_requested
tool_started
tool_progress
tool_finished
tool_failed
model_finished
task_completed
task_cancelled
```

The UI should not be responsible for implementing the tools themselves.

---

## 22. Reliability requirements

Rectury must be designed for failure.

### Tool failures

A tool may fail because:

- the application is not installed;
- a path does not exist;
- permissions are missing;
- the internet is unavailable;
- a UI element moved;
- a command timed out;
- a service rejected authentication;
- the model supplied invalid arguments.

Each failure should return a structured result.

### Retry rules

Rectury may retry when:

- the error is temporary;
- the retry is safe;
- the retry does not duplicate an external action.

Rectury should not automatically retry:

- purchases;
- messages;
- uploads;
- deletions;
- form submissions;
- payments.

### Maximum steps

Every task needs a maximum number of model/tool iterations to prevent infinite loops.

### Verification

Important tasks should have a verification step before reporting success.

---

## 23. Platform strategy

### Initial platform

Choose one operating system as the first supported platform.

A practical choice is Windows because the current development environment already uses it.

### Later platforms

- macOS;
- Linux.

### Cross-platform design

Keep platform-specific code behind separate implementations.

Example concept:

```text
open_application
├── windows implementation
├── macOS implementation
└── Linux implementation
```

The model should request the same tool regardless of operating system.

---

## 24. Open-source strategy

Rectury can remain open source and still become a sustainable business.

### Open-source core

Possible public components:

- terminal UI;
- agent loop;
- tool schemas;
- local tools;
- provider integrations;
- memory system;
- plugin SDK;
- permission framework.

### Possible paid services

- hosted model access;
- account synchronization;
- encrypted cloud memory;
- multi-device support;
- team workspaces;
- centralized permission policies;
- audit logs;
- enterprise authentication;
- managed integrations;
- priority support;
- private deployment assistance.

### Important positioning

Do not claim that open source alone is the main differentiator.

The product value is:

```text
General computer control
+
Reliable tool execution
+
Clear permissions
+
Terminal-first UX
+
Extensibility
+
Local-first control
```

---

## 25. Business model possibilities

### Bring your own API key

Free/open-source users provide their own model API key.

### Managed model access

Users pay Rectury for simplified model access without configuring providers.

### Team plan

Possible features:

- shared configurations;
- shared workflows;
- approved tool policies;
- team memory;
- audit history;
- centralized billing.

### Enterprise plan

Possible features:

- private deployment;
- local models;
- SSO;
- advanced audit logs;
- custom tools;
- support agreements;
- security controls.

### Tool marketplace

Long-term possibility:

- community tools;
- verified tools;
- commercial integrations;
- revenue sharing.

This should only be considered after a stable plugin and permission system exists.

---

## 26. MVP definition

The first MVP should prove that Rectury is an agent, not merely a chat interface.

### Required MVP capabilities

1. Terminal interface.
2. Connection to one LLM provider.
3. Streaming responses.
4. Tool schema loading.
5. Tool-call detection.
6. Tool execution.
7. Tool result returned to the model.
8. At least three working tools.
9. Basic permission prompts.
10. Clear tool status in the UI.
11. Error handling.
12. User cancellation.

### Recommended first tools

- `get_current_directory`
- `list_files`
- `read_file`
- `open_application`

### MVP demonstration

```text
User: What files are in this project?

Rectury:
● Reading current directory
● Listing project files
✓ 14 files found

This project contains…
```

Second demonstration:

```text
User: Open Steam.

Rectury:
● Opening Steam
✓ Steam opened successfully
```

A successful MVP proves the complete loop:

```text
User → Model → Tool → Result → Model → User
```

---

## 27. Development roadmap

### Phase 0 — Foundations

- repository initialized;
- virtual environment;
- dependency management;
- `.gitignore`;
- `.env.example`;
- model API connection;
- basic terminal UI.

### Phase 1 — Core agent loop

- conversation messages;
- tool schemas;
- detect tool calls;
- dispatch tool by name;
- return tool output;
- repeat until final response;
- maximum step limit;
- structured errors.

### Phase 2 — Streaming and responsive UI

- model streaming;
- Textual worker;
- text-delta events;
- tool status events;
- loading animation;
- cancellation.

### Phase 3 — Read-only tools

- current directory;
- list files;
- read file;
- search files;
- system info;
- running applications.

### Phase 4 — Permissions

- tool risk levels;
- approve once;
- reject;
- session trust;
- audit log;
- emergency stop.

### Phase 5 — Safe computer actions

- open application;
- open URL;
- create directory;
- copy file;
- clipboard actions;
- screenshots.

### Phase 6 — Controlled modifications

- write file;
- move file;
- rename file;
- command execution;
- recycle-bin deletion;
- undo support.

### Phase 7 — Browser agent

- browser session;
- structured page inspection;
- navigate;
- click;
- fill;
- download;
- upload;
- submit confirmation.

### Phase 8 — Visual desktop agent

- active window detection;
- accessibility tree;
- focus window;
- screen understanding;
- mouse and keyboard control;
- visual verification.

### Phase 9 — Communication

- drafts;
- email;
- messaging integrations;
- attachment handling;
- approval screens.

### Phase 10 — Memory

- recent-message window;
- session summary;
- task state;
- persistent memory;
- memory search;
- user memory controls.

### Phase 11 — Extensibility

- tool registry;
- plugin API;
- plugin metadata;
- plugin permissions;
- plugin validation;
- documentation for contributors.

### Phase 12 — Product maturity

- cross-platform support;
- installer;
- auto-update;
- configuration screen;
- telemetry only with opt-in;
- documentation;
- security review;
- release process.

---

## 28. Development priorities

When choosing what to build next, use this order:

1. Correctness.
2. Safety.
3. Reliability.
4. Clear user feedback.
5. Speed.
6. Visual polish.
7. Number of tools.

Do not prioritize adding many tools before the agent loop, permissions, and error handling are stable.

---

## 29. Non-goals for the first versions

Do not build all of the following immediately:

- multi-agent teams;
- voice control;
- mobile applications;
- autonomous purchases;
- full cross-platform support;
- cloud accounts;
- public tool marketplace;
- complex vector databases;
- always-on background control;
- remote computer control;
- unrestricted administrator access.

These may be considered later, but they should not delay the core agent loop.

---

## 30. Key technical challenges

### Tool-call reliability

The model may:

- call a nonexistent tool;
- omit required arguments;
- pass invalid paths;
- request unsafe actions;
- misunderstand the result.

Rectury must validate every call.

### GUI reliability

Raw mouse coordinates are fragile.

Prefer:

1. direct APIs;
2. structured browser automation;
3. accessibility APIs;
4. visual recognition;
5. coordinates as a last resort.

### Security

A general computer agent has access to sensitive resources.

Permissions, logs, secrets, cancellation, and isolation are essential.

### Context cost

Large histories and many tool descriptions increase latency and model cost.

Use selective context and tool loading where possible.

### Cross-platform complexity

Operating-system actions differ significantly.

Build one platform well before supporting all platforms.

### Verification

The agent needs to know whether an action actually succeeded.

This may require process checks, filesystem checks, browser state inspection, or screenshots.

---

## 31. Success metrics

### Technical metrics

- percentage of tool calls executed without schema errors;
- percentage of tasks completed successfully;
- average time to first streamed token;
- average tool execution time;
- number of failed or cancelled actions;
- retry rate;
- permission prompt acceptance rate;
- test coverage of tools.

### Product metrics

- successful tasks per user;
- returning users;
- number of installed tools;
- number of contributed tools;
- tasks completed without manual intervention;
- user-reported trust;
- user-reported time saved.

### Safety metrics

- destructive actions blocked;
- external actions requiring confirmation;
- accidental duplicate actions;
- sensitive information redacted;
- tasks cancelled successfully.

---

## 32. Project communication

Rectury should be presented honestly.

Avoid claims such as:

```text
Rectury can do anything on your computer.
```

Prefer:

```text
Rectury is an open-source Personal Computer Agent being built to operate applications, files, browser workflows, and development tools through natural language.
```

Early-stage communication can use:

```text
Building Rectury in public.
```

```text
A terminal-first Personal Computer Agent.
```

```text
From natural-language request to visible computer action.
```

---

## 33. Suggested public description

### One sentence

> Rectury is an open-source, terminal-first Personal Computer Agent that can understand requests, use tools, and operate your computer under your control.

### Short paragraph

> Rectury is an open-source Personal Computer Agent built for the terminal. Instead of only answering questions, it is designed to operate files, applications, browser workflows, development tools, and connected services through a transparent tool and permission system.

### Longer description

> Rectury is a terminal-first Personal Computer Agent designed to turn natural-language requests into visible, controlled computer actions. It connects language models to a modular tool system for files, applications, browsers, development workflows, communication, and automation. Every important action is shown to the user, and sensitive actions require explicit approval.

---

## 34. Suggested repository structure

This is a long-term direction, not a requirement to implement immediately.

```text
Rectury-Desktop/
├── agent.py
├── requirements.txt
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
│
├── ui/
│   ├── terminal.py
│   ├── messages.py
│   └── widgets.py
│
├── tools/
│   ├── tools.json
│   ├── registry.py
│   ├── filesystem/
│   ├── applications/
│   ├── system/
│   ├── browser/
│   ├── communication/
│   └── development/
│
├── core/
│   ├── agent_loop.py
│   ├── provider.py
│   ├── events.py
│   ├── permissions.py
│   └── task_state.py
│
├── memory/
│   ├── session.py
│   ├── summary.py
│   └── storage.py
│
├── config/
│   └── settings.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── docs/
    ├── PROJECT_BLUEPRINT.md
    ├── TOOLS.md
    ├── SECURITY.md
    └── CONTRIBUTING.md
```

Do not create every folder before it is needed. Refactor toward this structure as the project grows.

---

## 35. Definition of done for a tool

A tool is not complete only because it works once.

A tool is complete when:

- its schema is valid;
- its arguments are validated;
- it returns a consistent result;
- errors are handled;
- its risk level is defined;
- permission behavior is implemented;
- it does not expose secrets;
- it has tests;
- the UI displays its state;
- important results are verified;
- its documentation exists.

---

## 36. Definition of done for the MVP

The MVP is complete when a new user can:

1. Clone or install Rectury.
2. Configure a model API key.
3. Start Rectury from the terminal.
4. Enter a natural-language request.
5. See the response stream in real time.
6. See when Rectury requests a tool.
7. Approve a modifying action.
8. Watch the tool execute.
9. Receive a verified final result.
10. Stop the agent at any time.

---

## 37. Immediate next objectives

The recommended next objectives are:

### Objective 1

Complete the full tool loop with the current read-path tool:

```text
User asks
→ Grok requests tool
→ Rectury executes tool
→ Result returns to Grok
→ Grok gives final answer
```

### Objective 2

Add real-time model streaming without blocking the Textual interface.

### Objective 3

Create a consistent tool result format.

### Objective 4

Add `list_files`.

### Objective 5

Add `open_application`.

### Objective 6

Create the first permission prompt for modifying or sensitive actions.

### Objective 7

Add cancellation and a maximum number of agent steps.

### Objective 8

Record internal events so the UI can show:

```text
thinking
tool requested
tool running
tool completed
response streaming
```

---

## 38. Long-term ambition

The long-term ambition is for Rectury to become a trusted layer between the user and the computer.

Instead of learning every menu, application workflow, command, and integration, the user describes the desired outcome.

Rectury then:

- understands;
- plans;
- asks;
- acts;
- verifies;
- explains.

The final product should feel less like a chatbot and more like an operator that works with the user.

---

## 39. Final project statement

> Rectury is an open-source, terminal-first Personal Computer Agent. Its purpose is to transform natural-language goals into visible, controlled, and verifiable computer actions. It is designed to operate across files, applications, browsers, development workflows, communication services, and future integrations through a modular tool system. Rectury prioritizes user control, explicit permissions, local-first data, transparent execution, and extensibility.