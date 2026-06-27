from rich.markup import escape
from rich.style import Style
from rich.text import Text
from textual.widgets import Label

from core.tool_results import compact_text
from ui.visual import (
    THEME,
    compact_path,
    display_path,
    format_bytes,
    format_duration_ms,
    format_number,
    truncate_middle as visual_truncate_middle,
)


SYNTAX_THEME = "one-dark"
DIFF_ADD_BACKGROUND = THEME.diff_added
DIFF_REMOVE_BACKGROUND = THEME.diff_removed
DIFF_ADD_ACCENT = THEME.success
DIFF_REMOVE_ACCENT = THEME.error
DIFF_MUTED = THEME.secondary_text
DIFF_SEPARATOR = THEME.secondary_border
ACCENT = THEME.assistant
COMMAND_ACCENT = THEME.command
PERMISSION_ACCENT = THEME.permission
WARNING_ACCENT = THEME.warning
RESULT_PREFIX = "   "
RESULT_INDENT = "   "
MAX_ERROR_LINES = 10


TOOL_NAMES = {
    "list_files_in_dir": "Analyze",
    "list_reference_dir": "Analyze",
    "read_file": "Read",
    "read_image": "Read Image",
    "read_reference_file": "Read",
    "read_notebook": "Read Notebook",
    "delete_file": "Delete",
    "edit_file": "Modify",
    "multi_edit": "Modify",
    "edit_notebook": "Modify Notebook",
    "insert_notebook_cell": "Modify Notebook",
    "delete_notebook_cell": "Modify Notebook",
    "write_file": "Write",
    "memory_read": "Memory",
    "memory_write": "Memory",
    "mcp_list_servers": "MCP",
    "mcp_list_tools": "MCP",
    "mcp_call_tool": "MCP",
    "architect": "Architect",
    "run_command": "Run",
    "change_workspace": "Workspace",
    "glob": "Search",
    "grep": "Search",
    "grep_reference": "Search",
    "reference_add": "Reference",
    "reference_list": "Reference",
    "reference_remove": "Reference",
    "index_project": "Index",
    "index_reference": "Index",
    "project_overview": "Index",
    "reference_overview": "Index",
    "index_changed_files": "Index",
    "search_project": "Search",
    "search_reference_project": "Search",
    "search_symbols": "Search",
    "get_current_time": "Time",
    "think": "Think",
    "sticker_request": "Stickers",
    "self_reflect": "Inspect",
    "task": "Task",
    "todo_read": "Tasks",
    "todo_write": "Tasks",
    "checkpoint_history": "History",
    "undo_last_change": "Undo",
    "hook": "Hook",
}

TOOL_SPINNER_FRAMES = [
    "-",
    "\\",
    "|",
    "/",
]

def get_tool_target(tool_name, arguments):
    if tool_name in {"todo_read", "todo_write"}:
        return ""

    if tool_name in {"checkpoint_history", "undo_last_change"}:
        return arguments.get("file_path", "")

    if tool_name == "hook":
        return arguments.get("name") or arguments.get("event", "")

    if tool_name in {"list_files_in_dir", "list_reference_dir"}:
        return arguments.get("directory", "")

    if tool_name == "run_command":
        return arguments.get("command", "")

    if tool_name == "change_workspace":
        return arguments.get("new_path", "")

    if tool_name == "glob":
        return arguments.get("pattern", "")

    if tool_name in {"grep", "grep_reference"}:
        return arguments.get("pattern", "")

    if tool_name == "reference_add":
        return arguments.get("path", "")

    if tool_name == "reference_remove":
        return arguments.get("reference", "")

    if tool_name in {"search_project", "search_reference_project", "search_symbols"}:
        return arguments.get("query", "")

    if tool_name in {"index_project", "project_overview", "index_changed_files"}:
        return arguments.get("workspace", ".")

    if tool_name in {"index_reference", "reference_overview"}:
        return arguments.get("reference", "")

    if tool_name in {"memory_read", "memory_write"}:
        return arguments.get("file_path", "RECTURY.md")

    if tool_name in {
        "read_notebook",
        "edit_notebook",
        "insert_notebook_cell",
        "delete_notebook_cell",
    }:
        return arguments.get("file_path", "")

    if tool_name == "read_image":
        return arguments.get("file_path", "")

    if tool_name in {"mcp_list_tools", "mcp_call_tool"}:
        return arguments.get("server", "")

    if tool_name in {"task", "architect"}:
        return arguments.get("prompt") or arguments.get("task", "")

    return arguments.get("file_path", "")


def format_todos(todos):
    output = Text()
    status_styles = {
        "pending": DIFF_MUTED,
        "in_progress": WARNING_ACCENT,
        "completed": DIFF_ADD_ACCENT,
    }
    status_marks = {
        "pending": "[ ]",
        "in_progress": "[>]",
        "completed": "[x]",
    }

    if not todos:
        output.append("   no tasks", style=DIFF_MUTED)
        return output

    for index, todo in enumerate(todos):
        if index:
            output.append("\n")

        status = todo.get("status", "pending")
        output.append("   ")
        output.append(
            status_marks.get(status, "[ ]"),
            style=status_styles.get(status, DIFF_MUTED),
        )
        output.append(" ")
        output.append(str(todo.get("content", "")))
        output.append(" ")
        output.append(
            status.replace("_", " "),
            style=status_styles.get(status, DIFF_MUTED),
        )

    return output


def get_tool_name(tool_name, arguments):
    if (
        tool_name == "edit_file"
        and arguments.get("old_text") == ""
    ):
        return "Create"

    return TOOL_NAMES.get(tool_name, tool_name)


def shorten_path(value):
    return display_path(value)


def truncate_middle(value, limit=120):
    return visual_truncate_middle(value, limit)


def tool_heading(tool_name, arguments):
    display_name = get_tool_name(tool_name, arguments)
    target = shorten_path(get_tool_target(tool_name, arguments))

    if tool_name == "run_command":
        target = truncate_middle(target, 100)

    marker_style = COMMAND_ACCENT if tool_name == "run_command" else ACCENT
    heading = f"[bold {marker_style}]{escape(display_name)}[/bold {marker_style}]"

    if target:
        heading += f" [dim]{escape(target)}[/dim]"

    return heading


def append_result_line(output, text, style=DIFF_MUTED, prefix=RESULT_PREFIX):
    output.append("\n")
    output.append(prefix, style=DIFF_MUTED)
    output.append(str(text), style=style)


def result_duration(result):
    if not isinstance(result, dict):
        return ""

    return format_duration_ms(result.get("duration_ms"))


def duration_markup(result):
    duration = result_duration(result)
    return f" · {escape(duration)}" if duration else ""


def append_duration(output, result):
    duration = result_duration(result)

    if not duration:
        return

    output.append(" · ", style=DIFF_MUTED)
    output.append(duration, style=DIFF_MUTED)


def append_output_block(output, label, content, style=None, max_chars=3500):
    content = compact_text(content or "", max_chars).strip()

    if not content:
        return

    output.append("\n\n")
    output.append(RESULT_PREFIX, style=DIFF_MUTED)
    output.append(label, style=DIFF_MUTED)
    output.append("\n")
    output.append(content, style=style)


def compact_error(error, max_lines=MAX_ERROR_LINES):
    lines = str(error or "").strip().splitlines()

    if len(lines) <= max_lines:
        return "\n".join(lines)

    hidden = len(lines) - max_lines
    return "\n".join(lines[:max_lines] + [f"... (+{hidden} lines)"])


def format_diff(diff, max_lines=40):
    lines = diff.splitlines()
    formatted_lines = []

    for line in lines[:max_lines]:
        safe_line = escape(line)

        if line.startswith("+++") or line.startswith("---"):
            formatted_lines.append(f"[dim]{safe_line}[/dim]")
        elif line.startswith("+"):
            formatted_lines.append(f"[green]{safe_line}[/green]")
        elif line.startswith("-"):
            formatted_lines.append(f"[red]{safe_line}[/red]")
        elif line.startswith("@@"):
            formatted_lines.append(f"[dim]{safe_line}[/dim]")
        else:
            formatted_lines.append(safe_line)

    if len(lines) > max_lines:
        formatted_lines.append(
            f"[dim]... {len(lines) - max_lines} more diff lines[/dim]"
        )

    return "\n".join(formatted_lines)


def format_tool_started(tool_name, arguments, spinner_frame="-"):
    display_name = (
        get_tool_name(tool_name, arguments)
        if arguments
        else TOOL_NAMES.get(
            tool_name,
            f"Running {tool_name}",
        )
    )
    marker_style = COMMAND_ACCENT if tool_name == "run_command" else ACCENT
    heading = f"[bold {marker_style}]{escape(display_name)}[/bold {marker_style}]"
    target = shorten_path(get_tool_target(tool_name, arguments))

    if tool_name == "run_command":
        target = truncate_middle(target, 100)

    if target:
        heading += f" [dim]{escape(target)}[/dim]"

    return f"{heading} {spinner_frame}"


def format_line_number(value, width=4):
    if value is None:
        return " " * width

    return f"{value:>{width}}"


def highlight_code(content, file_path):
    return Text(str(content or "").rstrip())


def format_structured_diff(
    diff_lines,
    file_path="",
    max_lines=60,
    dim=False,
    width=100,
):
    output = Text()
    numbered_rows = [
        row
        for row in diff_lines
        if row["type"] != "separator"
    ]
    largest_line = max(
        [
            row.get("old_line") or 0
            for row in numbered_rows
        ]
        + [
            row.get("new_line") or 0
            for row in numbered_rows
        ]
        + [1]
    )
    line_width = max(3, len(str(largest_line)))
    content_width = max(20, width)

    for row_index, row in enumerate(diff_lines[:max_lines]):
        if row_index:
            output.append("\n")

        if row["type"] == "separator":
            output.append(
                f"{' ' * (line_width * 2 + 4)}...",
                style=DIFF_SEPARATOR,
            )
            continue

        old_line = format_line_number(
            row.get("old_line"),
            line_width,
        )
        new_line = format_line_number(
            row.get("new_line"),
            line_width,
        )
        code = highlight_code(
            row.get("content", ""),
            file_path,
        )
        line_start = len(output)

        if row["type"] == "remove":
            output.append(old_line, style=DIFF_MUTED)
            output.append(f" {' ' * line_width} ")
            output.append(
                "- ",
                style=Style(color=DIFF_REMOVE_ACCENT, bold=True),
            )
            output.append("  ", style=DIFF_MUTED)
            code.stylize(
                Style(
                    dim=dim,
                )
            )
            output.append_text(code)
            padding = max(
                0,
                content_width - (len(output) - line_start),
            )
            output.append(" " * padding)
            output.stylize(
                Style(
                    bgcolor=DIFF_REMOVE_BACKGROUND,
                    dim=dim,
                ),
                line_start,
                len(output),
            )
        elif row["type"] == "add":
            output.append(" " * line_width)
            output.append(
                f" {new_line} ",
                style=DIFF_MUTED,
            )
            output.append(
                "+ ",
                style=Style(color=DIFF_ADD_ACCENT, bold=True),
            )
            output.append("  ", style=DIFF_MUTED)
            code.stylize(
                Style(
                    dim=dim,
                )
            )
            output.append_text(code)
            padding = max(
                0,
                content_width - (len(output) - line_start),
            )
            output.append(" " * padding)
            output.stylize(
                Style(
                    bgcolor=DIFF_ADD_BACKGROUND,
                    dim=dim,
                ),
                line_start,
                len(output),
            )
        else:
            output.append(
                f"{old_line} {new_line} ",
                style=DIFF_MUTED,
            )
            output.append("    ", style=DIFF_SEPARATOR)
            if dim:
                code.stylize("dim")
            output.append_text(code)

    if len(diff_lines) > max_lines:
        output.append("\n")
        output.append(
            f"{' ' * (line_width * 2 + 4)}... "
            f"{len(diff_lines) - max_lines} more lines",
            style=DIFF_SEPARATOR,
        )

    if not output:
        output.append("(no changes)", style="dim")

    return output


def format_edit_preview(preview, width=100):
    return format_structured_diff(
        preview.get("diff_lines", []),
        preview.get("file_path", ""),
        width=width,
    )


def format_tool_finished(tool_name, arguments, result, width=100):
    heading = tool_heading(tool_name, arguments)

    if result.get("rejected"):
        output = Text.from_markup(heading)
        append_result_line(output, "request rejected", DIFF_REMOVE_ACCENT)
        diff_lines = result.get("diff_lines", [])

        if diff_lines:
            output.append("\n\n")
            output.append_text(
                format_structured_diff(
                    diff_lines,
                    result.get("file_path")
                    or get_tool_target(tool_name, arguments),
                    dim=True,
                    width=width,
                )
            )
            return output

        return output

    if result.get("error") and tool_name != "run_command":
        output = Text.from_markup(heading)
        append_result_line(
            output,
            f"error: {compact_error(result['error'])}",
            DIFF_REMOVE_ACCENT,
        )
        return output

    if tool_name in {"read_file", "read_reference_file"}:
        returned_lines = result.get("returned_lines", 0)
        source = (
            f"   [dim]reference: {escape(shorten_path(result.get('reference', '')))}[/dim]\n"
            if tool_name == "read_reference_file" and result.get("reference")
            else ""
        )
        return (
            f"{heading}\n"
            f"{source}"
            f"   [dim]{format_number(returned_lines)} lines loaded"
            f"{duration_markup(result)}[/dim]"
        )

    if tool_name in {"list_files_in_dir", "list_reference_dir"}:
        file_count = len(result.get("files", []))
        noun = "file" if file_count == 1 else "files"
        source = (
            f"   [dim]reference: {escape(shorten_path(result.get('reference', '')))}[/dim]\n"
            if tool_name == "list_reference_dir" and result.get("reference")
            else ""
        )
        return (
            f"{heading}\n"
            f"{source}"
            f"   [dim]{file_count} {noun} discovered"
            f"{duration_markup(result)}[/dim]"
        )

    if tool_name == "glob":
        files = result.get("files", [])
        count = len(files)
        truncated = result.get("truncated", False)
        extra = " (truncated)" if truncated else ""
        output = Text.from_markup(heading)
        output.append(
            f"\n   {count} file{'s' if count != 1 else ''} found{extra}",
            style=DIFF_MUTED,
        )
        append_duration(output, result)

        for path in files[:10]:
            output.append("\n   ")
            output.append(shorten_path(path))

        return output

    if tool_name in {"grep", "grep_reference"}:
        matches = result.get("matches", [])
        count = len(matches)
        truncated = result.get("truncated", False)
        extra = " (truncated)" if truncated else ""
        pattern = arguments.get("pattern", "")
        search_path = arguments.get("path", ".")
        glob_pat = arguments.get("glob", "**/*")
        detail = f"pattern=\"{pattern}\" path=\"{search_path}\" glob=\"{glob_pat}\""
        source = (
            f"   [dim]reference: {escape(shorten_path(result.get('reference', '')))}[/dim]\n"
            if tool_name == "grep_reference" and result.get("reference")
            else ""
        )
        return (
            f"{heading}\n"
            f"{source}"
            f"   [dim]{detail}[/dim]\n"
            f"   [dim]{count} match{'es' if count != 1 else ''} found{extra}"
            f"{duration_markup(result)}[/dim]"
        )

    if tool_name in {"reference_add", "reference_remove", "reference_list"}:
        output = Text.from_markup(heading)
        references = result.get("references", [])

        if tool_name == "reference_add":
            output.append("\n   added ", style=DIFF_ADD_ACCENT)
            output.append(shorten_path(result.get("path", "")))
        elif tool_name == "reference_remove":
            output.append("\n   removed ", style=DIFF_REMOVE_ACCENT)
            output.append(shorten_path(result.get("removed", "")))
        else:
            output.append(
                f"\n   {result.get('total', len(references))} reference paths",
                style=DIFF_MUTED,
            )

        append_duration(output, result)

        if references:
            for item in references:
                output.append("\n   ")
                output.append(str(item.get("index", "")), style=WARNING_ACCENT)
                output.append(" ")
                output.append(shorten_path(item.get("path", "")), style=DIFF_MUTED)
        else:
            output.append("\n   no reference paths", style=DIFF_MUTED)

        return output

    if tool_name in {"index_project", "project_overview", "index_reference", "reference_overview"}:
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(result.get('files_indexed', 0))} files indexed",
            style=DIFF_MUTED,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"index {result.get('index_status', 'unknown')}",
            style=WARNING_ACCENT,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"{format_number(result.get('symbols', 0))} symbols",
            style=WARNING_ACCENT,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"{format_number(result.get('imports', 0))} imports",
            style=DIFF_MUTED,
        )
        append_duration(output, result)

        if result.get("reference"):
            output.append("\n   reference ", style=DIFF_MUTED)
            output.append(shorten_path(result.get("reference", "")), style=DIFF_MUTED)

        stats = result.get("stats", {})
        if stats:
            output.append("\n   ")
            output.append(
                f"{format_number(stats.get('indexed', 0))} indexed",
                style=DIFF_ADD_ACCENT,
            )
            output.append(" · ", style=DIFF_MUTED)
            output.append(
                f"{format_number(stats.get('reused', 0))} reused",
                style=DIFF_MUTED,
            )
            output.append(" · ", style=DIFF_MUTED)
            output.append(
                f"{format_number(stats.get('changed', 0))} changed",
                style=WARNING_ACCENT,
            )
            output.append(" · ", style=DIFF_MUTED)
            output.append(
                f"{format_number(stats.get('removed', 0))} removed",
                style=DIFF_REMOVE_ACCENT,
            )

        important_files = result.get("important_files", [])[:8]

        if important_files:
            output.append("\n")
            for item in important_files:
                output.append("\n   ")
                output.append(shorten_path(item.get("path", "")))
                output.append(
                    f"  score {format_number(item.get('importance', 0))}",
                    style=DIFF_MUTED,
                )

        return output

    if tool_name == "search_symbols":
        matches = result.get("matches", [])
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(result.get('total', len(matches)))} symbol matches",
            style=DIFF_MUTED,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"index {result.get('index_status', 'unknown')}",
            style=WARNING_ACCENT,
        )
        append_duration(output, result)

        for item in matches[:10]:
            output.append("\n   ")
            output.append(shorten_path(item.get("file", "")))
            output.append(f":{item.get('line', 1)} ", style=DIFF_MUTED)
            output.append(str(item.get("kind", "symbol")), style=DIFF_MUTED)
            output.append(" ")
            output.append(str(item.get("name", "")), style=WARNING_ACCENT)

        return output

    if tool_name in {"search_project", "search_reference_project"}:
        results = result.get("results", [])
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(result.get('total', len(results)))} ranked results",
            style=DIFF_MUTED,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"index {result.get('index_status', 'unknown')}",
            style=WARNING_ACCENT,
        )

        if result.get("reference"):
            output.append(" · ", style=DIFF_MUTED)
            output.append("reference", style=DIFF_MUTED)

        append_duration(output, result)

        for item in results[:10]:
            output.append("\n   ")
            output.append(shorten_path(item.get("file", "")))
            output.append(
                f"  score {format_number(item.get('score', 0))}",
                style=DIFF_MUTED,
            )

            reasons = item.get("reasons", [])
            if reasons:
                output.append("  ")
                output.append(", ".join(reasons[:4]), style=WARNING_ACCENT)

            symbols = item.get("symbols", [])
            if symbols:
                symbol = symbols[0]
                output.append(
                    f"\n      {symbol.get('kind', 'symbol')} "
                    f"{symbol.get('name', '')}:{symbol.get('line', 1)}",
                    style=DIFF_MUTED,
                )

            content_matches = item.get("content_matches", [])
            if content_matches:
                match = content_matches[0]
                output.append(
                    f"\n      line {match.get('line', 1)}: ",
                    style=DIFF_MUTED,
                )
                output.append(str(match.get("text", ""))[:120])

        return output

    if tool_name == "index_changed_files":
        changed = result.get("changed", [])
        missing = result.get("missing", [])
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(len(changed))} changed",
            style=WARNING_ACCENT if changed else DIFF_MUTED,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"{format_number(len(missing))} missing",
            style=DIFF_REMOVE_ACCENT if missing else DIFF_MUTED,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"index {result.get('index_status', 'unknown')}",
            style=WARNING_ACCENT,
        )
        append_duration(output, result)

        for path in changed[:8]:
            output.append("\n   changed ", style=WARNING_ACCENT)
            output.append(shorten_path(path))

        for path in missing[:8]:
            output.append("\n   missing ", style=DIFF_REMOVE_ACCENT)
            output.append(shorten_path(path))

        return output

    if tool_name in {
        "delete_file",
        "edit_file",
        "multi_edit",
        "edit_notebook",
        "insert_notebook_cell",
        "delete_notebook_cell",
    }:
        additions = result.get("additions", 0)
        removals = result.get("removals", 0)
        output = Text.from_markup(heading)

        if tool_name == "multi_edit":
            output.append(
                f"\n   {result.get('edit_count', 0)} replacements",
                style=DIFF_MUTED,
            )
        elif tool_name in {
            "edit_notebook",
            "insert_notebook_cell",
            "delete_notebook_cell",
        }:
            output.append(
                f"\n   cell {result.get('cell_index')}",
                style=DIFF_MUTED,
            )

        output.append("\n   ")
        if additions or removals:
            output.append(f"+{additions}", style=DIFF_ADD_ACCENT)
            output.append(" ", style=DIFF_MUTED)
            output.append(f"-{removals}", style=DIFF_REMOVE_ACCENT)
        else:
            output.append("file updated", style=DIFF_MUTED)

        append_duration(output, result)

        if result.get("index_status"):
            output.append("\n   ")
            output.append(
                f"index {result.get('index_status')}",
                style=DIFF_MUTED,
            )

        diff_lines = result.get("diff_lines", [])

        if diff_lines:
            output.append("\n\n")
            output.append_text(
                format_structured_diff(
                    diff_lines,
                    result.get("file_path")
                    or get_tool_target(tool_name, arguments),
                    width=width,
                )
            )
            return output

        return output

    if tool_name == "run_command":
        cmd = arguments.get("command", "")
        cwd = arguments.get("cwd", ".")
        rc = result.get("returncode")
        duration = result.get("duration_ms")
        safe = result.get("safe", False)
        status = "safe" if safe else "reviewed"
        running = result.get("running", False)
        output = Text.from_markup(
            f"{heading}\n"
            f"{RESULT_PREFIX}[dim]command: {escape(cmd)}[/dim]\n"
            f"{RESULT_INDENT}[dim]cwd: {escape(cwd)}[/dim]\n"
            f"{RESULT_INDENT}[dim]trust: {escape(status)}[/dim]"
        )
        if duration is not None:
            output.append(f" · {format_duration_ms(duration)}", style=DIFF_MUTED)
        if running:
            append_result_line(output, "running", WARNING_ACCENT)
        elif result.get("error"):
            append_result_line(
                output,
                f"error: {compact_error(result['error'])}",
                DIFF_REMOVE_ACCENT,
            )
        elif rc != 0:
            append_result_line(output, f"exit {rc}", DIFF_REMOVE_ACCENT)
        else:
            append_result_line(output, "exit 0", DIFF_MUTED)

        append_output_block(output, "stdout", result.get("stdout", ""))
        append_output_block(
            output,
            "stderr",
            result.get("stderr", ""),
            DIFF_REMOVE_ACCENT,
        )

        return output

    if tool_name in {"write_file", "memory_write"}:
        path = result.get("file_path", arguments.get("file_path", ""))
        size = result.get("bytes_written", 0)
        additions = result.get("additions", 0)
        removals = result.get("removals", 0)
        output = Text.from_markup(
            f"{heading}\n"
            f"   [dim]file: {escape(shorten_path(path))}[/dim]"
        )
        if tool_name == "write_file":
            output.append(f"\n   {format_bytes(size)} written", style=DIFF_MUTED)
            if additions or removals:
                output.append("  ")
                output.append(f"+{additions}", style=DIFF_ADD_ACCENT)
                output.append(" ")
                output.append(f"-{removals}", style=DIFF_REMOVE_ACCENT)
            append_duration(output, result)
        else:
            output.append(
                f"\n   {result.get('mode', 'append')} project memory",
                style=DIFF_MUTED,
            )
            append_duration(output, result)
        if result.get("index_status"):
            output.append("\n   ")
            output.append(
                f"index {result.get('index_status')}",
                style=DIFF_MUTED,
            )
        diff_lines = result.get("diff_lines", [])

        if diff_lines:
            output.append("\n\n")
            output.append_text(
                format_structured_diff(
                    diff_lines,
                    result.get("file_path")
                    or get_tool_target(tool_name, arguments),
                    width=width,
                )
            )

        return output

    if tool_name == "memory_read":
        files = result.get("files", [])
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(len(files))} memory file{'s' if len(files) != 1 else ''}",
            style=DIFF_MUTED,
        )
        append_duration(output, result)
        for path in files[:8]:
            output.append("\n   ")
            output.append(shorten_path(path))
        return output

    if tool_name == "read_notebook":
        output = Text.from_markup(heading)
        output.append(
            f"\n   {result.get('total_cells', 0)} cells",
            style=DIFF_MUTED,
        )
        append_duration(output, result)
        if result.get("truncated"):
            output.append(" · truncated", style=WARNING_ACCENT)
        return output

    if tool_name == "read_image":
        output = Text.from_markup(heading)
        size = result.get("bytes", 0)
        dimensions = (
            f"{result.get('width')}x{result.get('height')}"
            if result.get("width") and result.get("height")
            else "unknown size"
        )
        output.append(
            f"\n   {result.get('mime_type', 'image')} · {format_bytes(size)} · {dimensions}",
            style=DIFF_MUTED,
        )
        append_duration(output, result)
        if result.get("data_included"):
            output.append("\n   image data included", style=DIFF_ADD_ACCENT)
        return output

    if tool_name == "think":
        return f"{heading}\n   [dim]thought logged{duration_markup(result)}[/dim]"

    if tool_name == "task":
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(result.get('tool_uses', 0))} tool uses",
            style=DIFF_MUTED,
        )
        append_duration(output, result)
        summary = compact_text(result.get("summary", ""), 2500).strip()
        if summary:
            output.append("\n\n")
            output.append(summary)
        return output

    if tool_name == "architect":
        output = Text.from_markup(heading)
        append_result_line(
            output,
            f"completed{duration_markup(result)}",
            DIFF_MUTED,
        )
        plan = compact_text(result.get("plan", ""), 3000).strip()
        if plan:
            output.append("\n\n")
            output.append(plan)
        return output

    if tool_name in {"mcp_list_servers", "mcp_list_tools", "mcp_call_tool"}:
        output = Text.from_markup(heading)
        if tool_name == "mcp_list_servers":
            output.append(
                f"\n   {result.get('total', 0)} configured servers",
                style=DIFF_MUTED,
            )
        elif result.get("server"):
            output.append(f"\n   server {result.get('server')}", style=DIFF_MUTED)
        append_duration(output, result)
        return output

    if tool_name in {"todo_read", "todo_write"}:
        counts = result.get("counts", {})
        output = Text.from_markup(heading)
        output.append("\n   ")
        output.append(
            f"{format_number(counts.get('completed', 0))} completed",
            style=DIFF_ADD_ACCENT,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"{format_number(counts.get('in_progress', 0))} active",
            style=WARNING_ACCENT,
        )
        output.append(" · ", style=DIFF_MUTED)
        output.append(
            f"{format_number(counts.get('pending', 0))} pending",
            style=DIFF_MUTED,
        )
        append_duration(output, result)
        output.append("\n")
        output.append_text(format_todos(result.get("todos", [])))
        return output

    if tool_name == "checkpoint_history":
        checkpoints = result.get("checkpoints", [])
        output = Text.from_markup(heading)
        output.append(
            f"\n   {format_number(result.get('total', 0))} checkpoints",
            style=DIFF_MUTED,
        )
        append_duration(output, result)

        if not checkpoints:
            output.append("\n   no file changes to undo", style=DIFF_MUTED)
            return output

        for item in checkpoints:
            output.append("\n   ")
            output.append(str(item.get("id", "")), style=WARNING_ACCENT)
            output.append(" ")
            output.append(str(item.get("action", "")), style=DIFF_MUTED)
            output.append(" ")
            output.append(shorten_path(item.get("file_path", "")))
            output.append(
                f" +{item.get('additions', 0)} -{item.get('removals', 0)}",
                style=DIFF_MUTED,
            )

        return output

    if tool_name == "undo_last_change":
        output = Text.from_markup(heading)
        undone = result.get("undone", {})
        path = result.get("file_path", "")
        output.append("\n   reverted ", style=DIFF_MUTED)
        output.append(str(undone.get("id", "")), style=WARNING_ACCENT)
        if path:
            output.append(f" {shorten_path(path)}", style=DIFF_MUTED)
        append_duration(output, result)

        diff_lines = result.get("diff_lines", [])

        if diff_lines:
            output.append("\n\n")
            output.append_text(
                format_structured_diff(
                    diff_lines,
                    path,
                    width=width,
                )
            )

        return output

    if tool_name == "get_current_time":
        return (
            f"{heading}\n"
            f"   [dim]{escape(str(result.get('time', result)))}"
            f"{duration_markup(result)}[/dim]"
        )

    if tool_name == "hook":
        output = Text.from_markup(heading)
        event = result.get("event") or arguments.get("event", "")
        command = result.get("command") or arguments.get("command", "")
        nested = result.get("result", {})
        append_result_line(output, f"event: {event}", DIFF_MUTED)

        if command:
            append_result_line(output, f"command: {command}", DIFF_MUTED)

        if result.get("error"):
            append_result_line(
                output,
                f"error: {compact_error(result.get('error'))}",
                DIFF_REMOVE_ACCENT,
            )
            return output

        if nested:
            rc = nested.get("returncode")
            duration = nested.get("duration_ms")

            if duration is not None:
                append_result_line(
                    output,
                    format_duration_ms(duration),
                    DIFF_MUTED,
                )

            if nested.get("error"):
                append_result_line(
                    output,
                    f"error: {compact_error(nested.get('error'))}",
                    DIFF_REMOVE_ACCENT,
                )
            elif rc not in {None, 0}:
                append_result_line(output, f"exit {rc}", DIFF_REMOVE_ACCENT)
            else:
                append_result_line(output, "completed", DIFF_ADD_ACCENT)

            append_output_block(
                output,
                "stdout",
                nested.get("stdout", ""),
                max_chars=2000,
            )
            append_output_block(
                output,
                "stderr",
                nested.get("stderr", ""),
                DIFF_REMOVE_ACCENT,
                max_chars=2000,
            )
        else:
            append_result_line(output, "completed", DIFF_ADD_ACCENT)

        return output

    return f"{heading}\n   [dim]completed{duration_markup(result)}[/dim]"


class ToolMessage(Label):
    def __init__(self, tool_name, arguments=None):
        arguments = arguments or {}
        super().__init__(
            format_tool_started(tool_name, arguments),
            classes="tool-message",
            markup=True,
        )
        self.tool_name = tool_name
        self.arguments = arguments
        self.spinner_index = 0
        self.indicator_timer = None
        self.completed = False
        self.stream_result = {
            "running": True,
            "stdout": "",
            "stderr": "",
            "returncode": None,
            "safe": False,
            "duration_ms": None,
        }

    def on_mount(self):
        if self.completed:
            return

        self.indicator_timer = self.set_interval(
            0.08,
            self.update_spinner,
        )

    def update_spinner(self):
        if (
            self.tool_name == "run_command"
            and (
                self.stream_result.get("stdout")
                or self.stream_result.get("stderr")
            )
        ):
            return

        self.spinner_index = (
            self.spinner_index + 1
        ) % len(TOOL_SPINNER_FRAMES)
        self.update(
            format_tool_started(
                self.tool_name,
                self.arguments,
                TOOL_SPINNER_FRAMES[self.spinner_index],
            )
        )

    def start(self, arguments):
        self.arguments = arguments
        self.update(
            format_tool_started(
                self.tool_name,
                self.arguments,
                TOOL_SPINNER_FRAMES[self.spinner_index],
            )
        )

    def finish(self, result):
        self.completed = True

        if self.indicator_timer is not None:
            self.indicator_timer.stop()

        self.update(
            format_tool_finished(
                self.tool_name,
                self.arguments,
                result,
                width=max(20, self.size.width - 2),
            )
        )

    def append_stream_output(self, stream, content, duration_ms=None):
        if self.completed:
            return

        if stream not in {"stdout", "stderr"}:
            return

        if self.indicator_timer is not None:
            self.indicator_timer.stop()
            self.indicator_timer = None

        self.stream_result[stream] = (
            self.stream_result.get(stream, "") + str(content)
        )
        self.stream_result["duration_ms"] = duration_ms
        self.stream_result["running"] = True
        self.update(
            format_tool_finished(
                self.tool_name,
                self.arguments,
                self.stream_result,
                width=max(20, self.size.width - 2),
            )
        )

class PermissionMessage(Label):
    def __init__(self, tool_name, arguments, preview):
        self.tool_name = tool_name
        self.arguments = arguments
        self.preview = preview
        self.file_path = (
            preview.get("file_path")
            or get_tool_target(tool_name, arguments)
        )
        super().__init__(
            self.render_content(
                f"[{PERMISSION_ACCENT}]waiting for approval[/]",
                width=100,
            ),
            classes="permission-message",
            markup=True,
        )

    def on_mount(self):
        self.update(
            self.render_content(
                f"[{PERMISSION_ACCENT}]waiting for approval[/]",
                width=max(20, self.size.width - 4),
            )
        )

    def render_content(self, status, width=None):
        target = shorten_path(self.file_path)
        output = Text()
        output.append(
            get_tool_name(self.tool_name, self.arguments),
            style=Style(color=PERMISSION_ACCENT, bold=True),
        )
        if target:
            output.append(f" {target}", style=DIFF_MUTED)
        output.append("\n")

        if self.preview.get("diff_lines"):
            diff = format_edit_preview(
                self.preview,
                width=width or max(20, self.size.width - 4),
            )
            output.append("\n")
            output.append_text(diff)
        else:
            output.append("\n")
            output.append_text(
                self.permission_summary(),
            )

        output.append("\n\n   ")
        output.append_text(Text.from_markup(status))
        return output

    def permission_summary(self):
        output = Text()

        if self.tool_name == "run_command":
            command = self.arguments.get("command", "")
            cwd = self.arguments.get("cwd", ".")
            safe = self.preview.get("safe", False)
            output.append("command: ", style=DIFF_MUTED)
            output.append(command)
            output.append("\n")
            output.append("cwd: ", style=DIFF_MUTED)
            output.append(str(cwd))
            output.append("\n")
            output.append(
                "trust: ",
                style=DIFF_MUTED,
            )
            output.append("safe" if safe else "review")
            prefix = self.preview.get("prefix")
            if prefix:
                output.append("\n")
                output.append("prefix: ", style=DIFF_MUTED)
                output.append(str(prefix))
            return output

        if self.tool_name == "change_workspace":
            output.append("new workspace: ", style=DIFF_MUTED)
            output.append(str(self.arguments.get("new_path", "")))
            return output

        output.append("This action needs approval.", style=DIFF_MUTED)
        return output

    def finish(self, decision):
        if decision in {"once", "session"}:
            self.styles.display = "none"
            return

        statuses = {
            "reject": f"[{DIFF_REMOVE_ACCENT}]rejected[/]",
        }
        self.update(
            self.render_content(
                statuses.get(decision, statuses["reject"]),
                width=max(20, self.size.width - 4),
            )
        )
