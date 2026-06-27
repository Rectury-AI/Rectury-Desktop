import json


MAX_TOOL_RESULT_CHARS = 12000
MAX_LIST_ITEMS = 200
MAX_MATCHES = 100

HEAVY_KEYS = {
    "cells",
    "diff",
    "diff_lines",
    "edits",
    "thought",
    "updated_content",
    "content",
}


def compact_text(text, limit=MAX_TOOL_RESULT_CHARS):
    if text is None:
        return ""

    text = str(text)

    if len(text) <= limit:
        return text

    half = max(1, limit // 2)
    omitted = len(text) - half * 2
    return (
        text[:half].rstrip()
        + f"\n\n... {omitted} characters omitted ...\n\n"
        + text[-half:].lstrip()
    )


def scrub_result(value):
    if isinstance(value, dict):
        return {
            key: scrub_result(inner)
            for key, inner in value.items()
            if key not in HEAVY_KEYS
        }

    if isinstance(value, list):
        return [scrub_result(item) for item in value[:MAX_LIST_ITEMS]]

    if isinstance(value, str):
        return compact_text(value, 2000)

    return value


def result_for_model(tool_name, arguments, result):
    if result.get("error"):
        return compact_text(
            f"{tool_name} failed: {result.get('error')}\n"
            f"code: {result.get('code', 'unknown')}"
        )

    if result.get("rejected"):
        return (
            f"{tool_name} was rejected by the user. Stop and wait for new "
            "instructions."
        )

    if result.get("duplicate_read_skipped"):
        return (
            f"Duplicate {tool_name} skipped. Reuse the previous successful "
            "read result for the same file, offset, and limit in this task."
        )

    if tool_name in {"read_file", "read_reference_file"}:
        if result.get("type") == "image":
            dimensions = (
                f"{result.get('width')}x{result.get('height')}"
                if result.get("width") and result.get("height")
                else "unknown dimensions"
            )
            data_note = (
                "\nImage data URL included for model inspection."
                if result.get("data_included")
                else f"\nImage data omitted: {result.get('data_omitted_reason', 'not requested')}."
            )
            data_url = (
                f"\n{compact_text(result.get('data_url', ''), 8000)}"
                if result.get("data_included")
                else ""
            )
            return compact_text(
                f"Read image {result.get('file_path')}: "
                f"{result.get('mime_type')}, {result.get('bytes')} bytes, "
                f"{dimensions}."
                f"{data_note}"
                f"{data_url}"
            )

        source = (
            f"Reference {result.get('reference')}. "
            if tool_name == "read_reference_file"
            else ""
        )
        header = (
            f"{source}Read {result.get('file_path')} "
            f"lines {result.get('offset', 1)}-"
            f"{result.get('offset', 1) + result.get('returned_lines', 0) - 1} "
            f"of {result.get('total_lines', 0)}."
        )
        if result.get("truncated"):
            header += " Output was truncated; read a narrower range if needed."

        return compact_text(header + "\n\n" + result.get("content", ""))

    if tool_name in {"list_files_in_dir", "list_reference_dir"}:
        if result.get("tree"):
            message = result["tree"]
            if result.get("truncated"):
                message = (
                    "There are more files than the recursive listing limit. "
                    "The first entries are included below:\n\n"
                    + message
                )
            return compact_text(message)

        files = result.get("files", [])
        visible = files[:MAX_LIST_ITEMS]
        suffix = (
            f"\n... {len(files) - len(visible)} more entries omitted ..."
            if len(files) > len(visible)
            else ""
        )
        source = (
            f"Reference {result.get('reference')}. "
            if tool_name == "list_reference_dir"
            else ""
        )
        return (
            f"{source}Listed {result.get('directory', arguments.get('directory', '.'))}. "
            f"{len(files)} entries found.\n"
            + "\n".join(visible)
            + suffix
        )

    if tool_name == "glob":
        files = result.get("files", [])
        visible = files[:MAX_LIST_ITEMS]
        suffix = (
            f"\n... {len(files) - len(visible)} more files omitted ..."
            if len(files) > len(visible) or result.get("truncated")
            else ""
        )
        return compact_text(
            f"Glob {arguments.get('pattern', result.get('pattern', ''))}: "
            f"{result.get('total', len(files))} files found."
            + ("\n" + "\n".join(visible) if visible else "\nNo files found.")
            + suffix
        )

    if tool_name == "git_status":
        return compact_text(
            "Git status:\n"
            f"repo: {result.get('repo_root')}\n"
            f"branch: {result.get('branch') or '(detached or unknown)'}\n"
            f"last commit: {result.get('last_commit') or '(none)'}\n\n"
            f"status:\n{result.get('status') or '(clean)'}\n"
            f"unstaged diff stat:\n{result.get('diff_stat') or '(none)'}\n"
            f"staged diff stat:\n{result.get('staged_diff_stat') or '(none)'}"
        )

    if tool_name == "read_image":
        dimensions = (
            f"{result.get('width')}x{result.get('height')}"
            if result.get("width") and result.get("height")
            else "unknown dimensions"
        )
        data_note = (
            "\nImage data URL included for model inspection."
            if result.get("data_included")
            else f"\nImage data omitted: {result.get('data_omitted_reason', 'not requested')}."
        )
        data_url = (
            f"\n{compact_text(result.get('data_url', ''), 8000)}"
            if result.get("data_included")
            else ""
        )
        return compact_text(
            f"Read image {result.get('file_path')}: "
            f"{result.get('mime_type')}, {result.get('bytes')} bytes, "
            f"{dimensions}."
            f"{data_note}"
            f"{data_url}"
        )

    if tool_name == "analyze_website":
        pages = result.get("pages", [])
        lines = [
            (
                f"Website analysis for {result.get('start_url')}: "
                f"{result.get('pages_fetched', 0)} pages fetched, "
                f"crawl={result.get('crawl')}, max_depth={result.get('max_depth')}."
            )
        ]

        for page in pages[:10]:
            lines.append(
                f"\nPage: {page.get('url')} "
                f"({page.get('status_code')}, {page.get('content_type', '')})"
            )
            if page.get("title"):
                lines.append(f"Title: {page.get('title')}")
            if page.get("meta"):
                meta = page.get("meta", {})
                description = meta.get("description") or meta.get("og:description")
                if description:
                    lines.append(f"Description: {description}")
            headings = page.get("headings", [])
            if headings:
                lines.append(
                    "Headings: "
                    + "; ".join(
                        f"{item.get('level')} {item.get('text')}"
                        for item in headings[:12]
                    )
                )
            if page.get("text_excerpt"):
                lines.append(
                    "Visible text excerpt:\n"
                    + compact_text(page.get("text_excerpt", ""), 2500)
                )
            internal = page.get("internal_links", [])
            if internal:
                lines.append(
                    "Internal links: "
                    + ", ".join(item.get("url", "") for item in internal[:20])
                )
            forms = page.get("forms", [])
            if forms:
                lines.append(
                    "Forms: "
                    + json.dumps(forms[:5], ensure_ascii=False)
                )

        site_links = result.get("site_links", {})
        lines.append(
            "\nDiscovered links: "
            f"{site_links.get('internal_total', 0)} internal, "
            f"{site_links.get('external_total', 0)} external."
        )

        errors = result.get("errors", [])
        if errors:
            lines.append(
                "Fetch errors: "
                + json.dumps(errors[:10], ensure_ascii=False)
            )

        limitations = result.get("limitations", [])
        if limitations:
            lines.append("Limitations: " + " ".join(limitations))

        return compact_text("\n".join(lines), 18000)

    if tool_name in {"grep", "grep_reference"}:
        if result.get("files") is not None:
            files = result.get("files", [])
            visible = files[:MAX_LIST_ITEMS]
            suffix = (
                f"\n... {len(files) - len(visible)} more files omitted ..."
                if len(files) > len(visible) or result.get("truncated")
                else ""
            )
            return compact_text(
                f"Found {result.get('total', len(files))} "
                f"file{'s' if result.get('total', len(files)) != 1 else ''}"
                + ("\n" + "\n".join(visible) if visible else "\nNo files found")
                + suffix
            )

        matches = result.get("matches", [])
        lines = [
            f"{match.get('file')}:{match.get('line')}: {match.get('text')}"
            for match in matches[:MAX_MATCHES]
        ]
        if len(matches) > MAX_MATCHES or result.get("truncated"):
            lines.append("... results truncated; use a narrower search ...")
        source = (
            f"Reference {result.get('reference')}. "
            if tool_name == "grep_reference"
            else ""
        )
        return (
            f"{source}Search found {len(matches)} matches."
            + ("\n" + "\n".join(lines) if lines else "")
        )

    if tool_name in {"reference_add", "reference_remove", "reference_list"}:
        references = result.get("references", [])
        lines = [
            f"- {item.get('index')}: {item.get('path')}"
            for item in references
        ]
        prefix = "Reference paths"

        if tool_name == "reference_add":
            prefix = f"Added reference path: {result.get('path')}"
        elif tool_name == "reference_remove":
            prefix = f"Removed reference path: {result.get('removed')}"

        return compact_text(
            f"{prefix}."
            + ("\n" + "\n".join(lines) if lines else "\nNo reference paths.")
        )

    if tool_name in {"index_project", "project_overview", "index_reference", "reference_overview"}:
        important = result.get("important_files", [])
        lines = [
            (
                f"- {item.get('path')} "
                f"(score {item.get('importance', 0)}, "
                f"{item.get('symbols', 0)} symbols, "
                f"{item.get('imports', 0)} imports)"
            )
            for item in important[:20]
        ]
        stats = result.get("stats", {})
        stats_text = (
            f"\nStats: scanned={stats.get('scanned', 0)}, "
            f"indexed={stats.get('indexed', 0)}, "
            f"reused={stats.get('reused', 0)}, "
            f"changed={stats.get('changed', 0)}, "
            f"removed={stats.get('removed', 0)}."
            if stats
            else ""
        )
        scope = (
            f"Reference index for {result.get('reference')}"
            if result.get("reference")
            else "Project index"
        )
        return compact_text(
            f"{scope}: {result.get('files_indexed', 0)} files, "
            f"{result.get('symbols', 0)} symbols, "
            f"{result.get('imports', 0)} imports. "
            f"Index status: {result.get('index_status', 'unknown')}."
            f"{stats_text}\n"
            f"Languages: {json.dumps(result.get('languages', {}), ensure_ascii=False)}\n"
            "Important files:\n"
            + ("\n".join(lines) if lines else "No important files.")
        )

    if tool_name == "search_symbols":
        matches = result.get("matches", [])
        lines = [
            (
                f"- {item.get('file')}:{item.get('line')} "
                f"{item.get('kind')} {item.get('name')}"
            )
            for item in matches[:MAX_MATCHES]
        ]
        return compact_text(
            f"Symbol search for {arguments.get('query', result.get('query', ''))}: "
            f"{result.get('total', len(matches))} matches. "
            f"Index status: {result.get('index_status', 'unknown')}."
            + ("\n" + "\n".join(lines) if lines else "\nNo matches.")
        )

    if tool_name in {"search_project", "search_reference_project"}:
        results = result.get("results", [])
        lines = []

        for item in results[:MAX_MATCHES]:
            detail = ", ".join(item.get("reasons", []))
            lines.append(
                f"- {item.get('file')} "
                f"(score {item.get('score', 0)}, {detail})"
            )

            for symbol in item.get("symbols", [])[:3]:
                lines.append(
                    f"  symbol: {symbol.get('kind')} "
                    f"{symbol.get('name')}:{symbol.get('line')}"
                )

            for match in item.get("content_matches", [])[:2]:
                lines.append(
                    f"  line {match.get('line')}: {match.get('text')}"
                )

        return compact_text(
            f"{'Reference search' if result.get('reference') else 'Project search'} "
            f"for {arguments.get('query', result.get('query', ''))}: "
            f"{result.get('total', len(results))} ranked results. "
            f"Index status: {result.get('index_status', 'unknown')}."
            + (f" Reference: {result.get('reference')}." if result.get("reference") else "")
            + ("\n" + "\n".join(lines) if lines else "\nNo results.")
        )

    if tool_name == "index_changed_files":
        changed = result.get("changed", [])
        missing = result.get("missing", [])
        lines = [f"- changed: {path}" for path in changed[:100]]
        lines.extend(f"- missing: {path}" for path in missing[:100])
        return compact_text(
            f"Index freshness: {result.get('total_changed', 0)} changed, "
            f"{result.get('total_missing', 0)} missing. "
            f"Index status: {result.get('index_status', 'unknown')}."
            + ("\n" + "\n".join(lines) if lines else "\nNo indexed files changed.")
        )

    if tool_name in {"todo_read", "todo_write"}:
        todos = result.get("todos", [])
        lines = [
            f"- [{todo.get('status')}] {todo.get('content')}"
            for todo in todos
        ]
        counts = result.get("counts", {})
        return compact_text(
            "Task list: "
            f"{counts.get('completed', 0)} completed, "
            f"{counts.get('in_progress', 0)} in progress, "
            f"{counts.get('pending', 0)} pending."
            + ("\n" + "\n".join(lines) if lines else "\nNo tasks.")
        )

    if tool_name == "checkpoint_history":
        checkpoints = result.get("checkpoints", [])
        lines = [
            (
                f"- {item.get('id')} {item.get('action')} "
                f"{item.get('file_path')} "
                f"(+{item.get('additions', 0)} -{item.get('removals', 0)})"
            )
            for item in checkpoints
        ]
        return compact_text(
            f"Checkpoint history: {result.get('total', 0)} total."
            + ("\n" + "\n".join(lines) if lines else "\nNo checkpoints.")
        )

    if tool_name == "undo_last_change":
        undone = result.get("undone", {})
        return compact_text(
            f"Undid checkpoint {undone.get('id')} for "
            f"{result.get('file_path')}."
        )

    if tool_name in {
        "delete_file",
        "edit_file",
        "multi_edit",
        "edit_notebook",
        "insert_notebook_cell",
        "delete_notebook_cell",
    }:
        if tool_name == "delete_file":
            action = "Deleted"
        else:
            action = "Created" if result.get("created") else "Updated"
        extra = ""

        if tool_name == "multi_edit":
            extra = f" Applied {result.get('edit_count', 0)} edits."
        elif tool_name in {
            "edit_notebook",
            "insert_notebook_cell",
            "delete_notebook_cell",
        }:
            extra = f" Updated cell {result.get('cell_index')}."

        return compact_text(
            f"{action} {result.get('file_path')} with "
            f"{result.get('additions', 0)} additions and "
            f"{result.get('removals', 0)} removals. "
            f"Index status: {result.get('index_status', 'unknown')}.{extra}\n\n"
            "Edited snippet with line numbers:\n"
            f"{result.get('snippet', '')}"
        )

    if tool_name in {"write_file", "memory_write"}:
        prefix = "Updated project memory" if tool_name == "memory_write" else "Wrote"
        return compact_text(
            f"{prefix} {result.get('file_path')} "
            f"({result.get('bytes_written', 0)} bytes). "
            f"Index status: {result.get('index_status', 'unknown')}.\n\n"
            f"{result.get('summary', '')}"
        )

    if tool_name == "memory_read":
        files = result.get("files", [])
        return compact_text(
            f"Read project memory. Files: {', '.join(files) if files else 'none'}.\n\n"
            f"{result.get('content', '')}"
        )

    if tool_name == "read_notebook":
        cells = result.get("cells", [])
        lines = []

        for cell in cells[:MAX_MATCHES]:
            source = compact_text(cell.get("source", ""), 800)
            lines.append(
                f"Cell {cell.get('index')} [{cell.get('type')}]\n{source}"
            )

            outputs = cell.get("outputs", [])
            if outputs:
                lines.append(
                    "Outputs:\n"
                    + "\n".join(
                        f"- {item.get('type')}: {compact_text(item.get('text', ''), 300)}"
                        for item in outputs[:3]
                    )
                )

        if result.get("truncated"):
            lines.append("... notebook cells truncated ...")

        return compact_text(
            f"Read notebook {result.get('file_path')}: "
            f"{result.get('total_cells', len(cells))} cells."
            + ("\n\n" + "\n\n".join(lines) if lines else "\nNo cells.")
        )

    if tool_name == "think":
        return "Thought logged. Use it to continue the task."

    if tool_name == "task":
        errors = result.get("errors", [])
        error_text = (
            "\nErrors:\n"
            + "\n".join(
                f"- {item.get('tool')}: {item.get('error')}"
                for item in errors[:20]
            )
            if errors
            else ""
        )
        return compact_text(
            f"Subagent completed with {result.get('tool_uses', 0)} tool uses.\n\n"
            f"{result.get('summary', '')}"
            f"{error_text}"
        )

    if tool_name == "architect":
        return compact_text(
            f"Architecture plan from {result.get('model', 'model')}:\n\n"
            f"{result.get('plan', '')}"
        )

    if tool_name in {"mcp_list_servers", "mcp_list_tools", "mcp_call_tool"}:
        return compact_text(
            f"MCP {tool_name} result:\n"
            f"{json.dumps(scrub_result(result), ensure_ascii=False, indent=2)}"
        )

    if tool_name == "run_command":
        stdout = compact_text(result.get("stdout", ""), 5000)
        stderr = compact_text(result.get("stderr", ""), 5000)
        return compact_text(
            f"Command: {result.get('command')}\n"
            f"cwd: {result.get('cwd')}\n"
            f"exit: {result.get('returncode')}\n\n"
            f"stdout:\n{stdout}\n\n"
            f"stderr:\n{stderr}"
        )

    return compact_text(json.dumps(scrub_result(result), ensure_ascii=False))
