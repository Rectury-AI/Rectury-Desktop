APP_CSS = """
Screen {
    background: transparent;
    padding: 2 4;
}

#chat {
    background: transparent;
    height: 1fr;
    scrollbar-size: 0 0;
    scrollbar-background: transparent;
    scrollbar-color: transparent;
}

#input-row {
    width: 100%;
    height: 1;
    layout: horizontal;
}

#prompt {
    width: 2;
    height: 1;
    content-align: left middle;
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

#message-input {
    width: 1fr;
    height: 1;
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
}

#message-input:focus {
    border: none;
}
"""
