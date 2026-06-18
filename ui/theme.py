APP_CSS = """
Screen {
    background: transparent;
    padding: 2 4;
}

#welcome-panel {
    width: 100%;
    height: auto;
    border: solid gray;
    padding: 1 2;
    margin-bottom: 3;
}

#welcome-title {
    width: 100%;
    color: white;
    text-style: bold;
    margin-bottom: 1;
}

#welcome-copy {
    width: 100%;
    color: #a0a0a0;
    text-wrap: wrap;
    margin-bottom: 1;
}

#welcome-note {
    width: 100%;
    color: #777777;
    text-wrap: wrap;
}

#agent-context {
    width: 100%;
    height: auto;
    margin: 0 1 2 1;
}

#agent-name {
    color: white;
    text-style: bold;
}

#status {
    color: #666666;
}

#app-meta {
    width: 100%;
    height: 1;
    content-align: center middle;
    color: gray;
}

#chat {
    background: transparent;
    height: 1fr;
    scrollbar-size: 0 0;
    scrollbar-background: transparent;
    scrollbar-color: transparent;
}

#prompt {
    width: 2;
    height: 100%;
    content-align: left bottom;
    background: transparent;
}

.user-message {
    background: transparent;
    border: solid gray;
    padding: 0 1;
    margin: 0 0 1 0;
    width: 100%;
    text-wrap: wrap;
}

.assistant-message {
    background: transparent;
    margin: 0 0 2 1;
    width: 100%;
    text-wrap: wrap;
}

#input-row {
    width: 100%;
    height: 1;
    max-height: 6;
    layout: horizontal;
    background: transparent;
    border: none;
    padding: 0 1;
}

#message-input {
    width: 1fr;
    height: 1;
    max-height: 6;
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;

    scrollbar-size: 1 1;
    scrollbar-color: gray;
    scrollbar-color-hover: white;
    scrollbar-color-active: white;
    scrollbar-background: transparent;
    scrollbar-background-hover: transparent;
    scrollbar-background-active: transparent;
}

#message-input:focus {
    border: none;
}
"""
