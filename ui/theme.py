APP_CSS = """
Screen {
    background: transparent;
    padding: 1 4;
}

#welcome-panel {
    width: 100%;
    height: auto;
    border: solid gray;
    padding: 1 2;
    margin-bottom: 1;
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
    padding: 0 0 1 0;
    scrollbar-size: 0 0;
    scrollbar-background: transparent;
    scrollbar-color: transparent;
}

#command-menu-row {
    display: none;
    width: 100%;
    height: auto;
    max-height: 6;
    margin: 0 0 1 0;
    padding: 0 1;
    background: transparent;
}

#command-menu-spacer {
    width: 0;
    height: 1;
    background: transparent;
}

#command-menu {
    width: 1fr;
    height: auto;
    padding: 0;
    border-left: solid #444444;
    color: #a0a0a0;
    background: transparent;
}

.command-option {
    display: none;
    width: 100%;
    height: 1;
    padding: 0 1;
    color: #a0a0a0;
    background: transparent;
}

.command-option.selected {
    color: black;
    background: #d0d0d0;
}

ConversationScreen {
    align: center middle;
    background: transparent;
    padding: 0;
}

#conversation-dialog {
    width: 70%;
    max-width: 90;
    height: auto;
    max-height: 70%;
    padding: 1 2;
    border: none;
    background: #161616;
}

#conversation-dialog-header {
    width: 100%;
    height: 1;
    margin-bottom: 1;
}

#conversation-dialog-title {
    width: 100%;
    height: 1;
    color: white;
    text-style: bold;
}

#conversation-dialog-help {
    width: 100%;
    height: 1;
    margin-bottom: 1;
    color: #777777;
}

#conversation-search-row {
    width: 100%;
    height: 1;
    margin-bottom: 1;
    background: transparent;
}

#conversation-search-label {
    width: 8;
    height: 1;
    color: #777777;
}

#conversation-search {
    width: 1fr;
    height: 1;
    padding: 0;
    border: none;
    background: transparent;
    color: white;
}

#conversation-search:focus {
    border: none;
    background: transparent;
}

#conversation-list {
    width: 100%;
    height: auto;
    max-height: 20;
    background: transparent;
    border: none;
    scrollbar-size: 1 1;
}

#conversation-list ListItem {
    width: 100%;
    height: 2;
    padding: 0 1;
    margin-bottom: 1;
    color: #a0a0a0;
    background: transparent;
}

#conversation-list > ListItem:hover {
    color: white;
    background: #303030;
}

#conversation-list > ListItem.-highlight {
    color: black;
    background: #d0d0d0;
}

.conversation-option {
    width: 100%;
    height: 2;
}

#conversation-empty {
    display: none;
    width: 100%;
    height: 2;
    padding: 0 1;
    color: #777777;
}

#conversation-dialog-controls {
    width: 100%;
    height: 1;
    margin-top: 1;
    color: #777777;
}

ModelScreen {
    align: center middle;
    background: transparent;
    padding: 0;
}

#model-dialog {
    width: 76%;
    max-width: 92;
    height: auto;
    max-height: 90%;
    padding: 1 2;
    border: none;
    background: #161616;
}

#model-dialog-header {
    width: 100%;
    height: 1;
    margin-bottom: 1;
}

#model-dialog-title {
    width: 1fr;
    height: 1;
    color: white;
    text-style: bold;
}

#model-dialog-escape {
    width: auto;
    height: 1;
    color: #777777;
}

#model-help {
    width: 100%;
    height: 1;
    margin-bottom: 1;
    color: #777777;
}

#model-list {
    width: 100%;
    height: auto;
    max-height: 12;
    margin-bottom: 1;
    background: transparent;
    border: none;
    scrollbar-size: 1 1;
}

#model-list ListItem {
    width: 100%;
    height: 2;
    padding: 0 1;
    color: #a0a0a0;
    background: transparent;
}

#model-list > ListItem:hover {
    color: white;
    background: #303030;
}

#model-list > ListItem.-highlight {
    color: black;
    background: #d0d0d0;
}

.model-option {
    width: 100%;
    height: 2;
}

.model-field-label {
    width: 100%;
    height: 1;
    color: #777777;
}

#model-provider,
#model-name,
#model-api-key,
#model-base-url {
    width: 100%;
    height: 1;
    padding: 0;
    margin-bottom: 1;
    border: none;
    background: transparent;
    color: white;
}

#model-provider:focus,
#model-name:focus,
#model-api-key:focus,
#model-base-url:focus {
    border: none;
    background: transparent;
}

#model-error {
    width: 100%;
    height: 1;
    color: #ff8080;
}

.permission-message {
    width: 100%;
    height: auto;
    margin: 0 0 2 1;
    padding: 0;
    background: transparent;
    text-wrap: wrap;
}

#prompt {
    width: 2;
    height: 100%;
    content-align: left bottom;
    background: transparent;
}

.user-message {
    background: transparent;
    border: solid #888888;
    padding: 0 1;
    margin: 0 0 1 0;
    width: 100%;
    text-wrap: wrap;
}

.assistant-message {
    background: transparent;
    margin: 0 0 2 1;
    width: 100%;
    padding: 0;
}

.assistant-message MarkdownBlock {
    margin: 0;
    padding: 0;
}

.assistant-message MarkdownFence {
    margin: 1 0;
    padding: 0 1;
    background: transparent;
}

.tool-message {
    background: transparent;
    margin: 0 0 2 1;
    padding: 0;
    width: 100%;
    color: #d0d0d0;
    text-wrap: wrap;
}

#input-row {
    width: 100%;
    height: 1;
    max-height: 6;
    layout: horizontal;
    background: transparent;
    border: none;
    margin: 0 0 1 0;
    padding: 0 1 0 0;
}

#usage-bar {
    width: 100%;
    height: 1;
    margin: 0;
    padding: 0 1 0 2;
    background: transparent;
    color: #6f6f6f;
    text-wrap: nowrap;
    text-style: dim;
}

#permission-input {
    display: none;
    width: 100%;
    height: 5;
    padding: 0;
    margin: 0 0 0 2;
    color: #d0d0d0;
    text-wrap: nowrap;
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

#message-input .text-area--cursor {
    color: #111111;
    background: #f0f0f0;
    text-style: none;
}
"""
