"""Incremental project index used to inspect projects without reading everything."""

import ast
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


INDEX_VERSION = 2
INDEX_FILE = ".rectury/index.json"
MAX_FILE_BYTES = 1_000_000
MAX_SYMBOLS_PER_FILE = 300
MAX_IMPORTS_PER_FILE = 200
MAX_CONTENT_SEARCH_BYTES = 160_000
MAX_CONTENT_MATCHES_PER_FILE = 3

INDEXED_SUFFIXES = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
}

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".rectury",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".idea",
    ".vscode",
}

IMPORTANT_NAMES = {
    "readme.md",
    "readme.mdx",
    "pyproject.toml",
    "package.json",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
    "requirements.txt",
    "poetry.lock",
    "uv.lock",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".env.example",
    "rectury.md",
    ".rectury.md",
    "agents.md",
    ".cursorrules",
    "copilot-instructions.md",
}

PYTHON_IMPORT_RE = re.compile(r"^(?:from\s+([\w.]+)\s+import|import\s+(.+))")
JS_IMPORT_RE = re.compile(
    r"(?:import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]|"
    r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)|"
    r"require\(\s*['\"]([^'\"]+)['\"]\s*\))"
)
JS_SYMBOL_PATTERNS = [
    ("class", re.compile(r"^\s*(?:export\s+default\s+|export\s+)?class\s+([A-Za-z_$][\w$]*)")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(")),
    ("function", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?[A-Za-z_$][\w$]*\s*=>")),
]


def current_time():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def index_path(root: Path) -> Path:
    return root / INDEX_FILE


def load_index(root: str | Path) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    path = index_path(root)

    if not path.exists():
        return empty_index(root)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return empty_index(root)

    if isinstance(data, dict) and "files" in data:
        return data

    if isinstance(data, dict):
        return {
            "version": 1,
            "root": str(root),
            "generated_at": "",
            "stats": {},
            "files": data,
        }

    return empty_index(root)


def empty_index(root: Path) -> dict[str, Any]:
    return {
        "version": INDEX_VERSION,
        "root": str(root),
        "generated_at": "",
        "stats": {},
        "files": {},
    }


def save_index(root: Path, data: dict[str, Any]) -> None:
    path = index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def should_skip_dir(name: str) -> bool:
    return name in IGNORED_DIRS or name.startswith(".cache")


def iter_indexable_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if not should_skip_dir(dirname)
        ]

        for filename in filenames:
            path = Path(dirpath) / filename

            if path.suffix.lower() not in INDEXED_SUFFIXES:
                continue

            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue

            yield path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 64), b""):
            digest.update(chunk)

    return digest.hexdigest()


def language_for(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascriptreact",
        ".ts": "typescript",
        ".tsx": "typescriptreact",
        ".json": "json",
        ".md": "markdown",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(suffix, suffix.lstrip(".") or "text")


def extract_python_symbols(path: Path, text: str) -> list[dict[str, Any]]:
    symbols = []

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return fallback_python_symbols(text)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            symbols.append(
                {
                    "name": node.name,
                    "kind": "class",
                    "line": getattr(node, "lineno", 1),
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                {
                    "name": node.name,
                    "kind": "function",
                    "line": getattr(node, "lineno", 1),
                }
            )

    return sorted(symbols, key=lambda item: item["line"])[:MAX_SYMBOLS_PER_FILE]


def fallback_python_symbols(text: str) -> list[dict[str, Any]]:
    symbols = []

    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()

        if stripped.startswith("def ") or stripped.startswith("async def "):
            name = stripped.split("def ", 1)[1].split("(", 1)[0].strip()
            symbols.append({"name": name, "kind": "function", "line": line_number})
        elif stripped.startswith("class "):
            name = stripped.split("class ", 1)[1].split("(", 1)[0].rstrip(":").strip()
            symbols.append({"name": name, "kind": "class", "line": line_number})

    return symbols[:MAX_SYMBOLS_PER_FILE]


def extract_js_symbols(text: str) -> list[dict[str, Any]]:
    symbols = []

    for line_number, line in enumerate(text.splitlines(), 1):
        for kind, pattern in JS_SYMBOL_PATTERNS:
            match = pattern.match(line)

            if match:
                symbols.append(
                    {
                        "name": match.group(1),
                        "kind": kind,
                        "line": line_number,
                    }
                )
                break

        if len(symbols) >= MAX_SYMBOLS_PER_FILE:
            break

    return symbols


def extract_symbols(path: Path, text: str) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()

    if suffix == ".py":
        return extract_python_symbols(path, text)

    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return extract_js_symbols(text)

    return []


def extract_python_imports(text: str) -> list[str]:
    imports = []

    try:
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    except SyntaxError:
        for line in text.splitlines():
            match = PYTHON_IMPORT_RE.match(line.strip())
            if not match:
                continue
            if match.group(1):
                imports.append(match.group(1))
            elif match.group(2):
                imports.extend(
                    part.strip().split(" as ", 1)[0]
                    for part in match.group(2).split(",")
                    if part.strip()
                )

    return sorted(set(imports))[:MAX_IMPORTS_PER_FILE]


def extract_js_imports(text: str) -> list[str]:
    imports = []

    for match in JS_IMPORT_RE.finditer(text):
        value = next((group for group in match.groups() if group), None)

        if value:
            imports.append(value)

    return sorted(set(imports))[:MAX_IMPORTS_PER_FILE]


def extract_imports(path: Path, text: str) -> list[str]:
    suffix = path.suffix.lower()

    if suffix == ".py":
        return extract_python_imports(text)

    if suffix in {".js", ".jsx", ".ts", ".tsx"}:
        return extract_js_imports(text)

    return []


def importance_for(relative_path: str, metadata: dict[str, Any]) -> tuple[int, list[str]]:
    path = Path(relative_path)
    name = path.name.lower()
    parts = {part.lower() for part in path.parts}
    score = 0
    reasons = []

    if name in IMPORTANT_NAMES:
        score += 80
        reasons.append("project config/doc")

    if name in {"main.py", "app.py", "agent.py", "cli.py", "__main__.py"}:
        score += 70
        reasons.append("entry point")

    if "core" in parts:
        score += 25
        reasons.append("core")

    if "tools" in parts or "commands" in parts:
        score += 20
        reasons.append("tooling")

    if "ui" in parts:
        score += 15
        reasons.append("ui")

    symbol_count = len(metadata.get("symbols", []))
    import_count = len(metadata.get("imports", []))

    if symbol_count:
        score += min(30, symbol_count)
        reasons.append(f"{symbol_count} symbols")

    if import_count:
        score += min(20, import_count)
        reasons.append(f"{import_count} imports")

    if metadata.get("size", 0) > 150_000:
        score -= 20
        reasons.append("large")

    return score, reasons


def index_file(root: Path, path: Path) -> dict[str, Any]:
    stat = path.stat()
    relative_path = str(path.relative_to(root))
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.count("\n") + (1 if text else 0)
    metadata = {
        "path": relative_path,
        "language": language_for(path),
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
        "sha256": file_hash(path),
        "lines": lines,
        "symbols": extract_symbols(path, text),
        "imports": extract_imports(path, text),
    }
    score, reasons = importance_for(relative_path, metadata)
    metadata["importance"] = score
    metadata["importance_reasons"] = reasons
    return metadata


def file_unchanged(path: Path, old_meta: dict[str, Any]) -> bool:
    try:
        stat = path.stat()
    except OSError:
        return False

    return (
        old_meta.get("mtime_ns") == stat.st_mtime_ns
        and old_meta.get("size") == stat.st_size
        and old_meta.get("version") == INDEX_VERSION
    )


def summarize_index(files: dict[str, Any]) -> dict[str, Any]:
    languages = {}
    symbol_total = 0
    import_total = 0

    for meta in files.values():
        language = meta.get("language", "unknown")
        languages[language] = languages.get(language, 0) + 1
        symbol_total += len(meta.get("symbols", []))
        import_total += len(meta.get("imports", []))

    important_files = [
        {
            "path": path,
            "importance": meta.get("importance", 0),
            "reasons": meta.get("importance_reasons", [])[:3],
            "symbols": len(meta.get("symbols", [])),
            "imports": len(meta.get("imports", [])),
            "lines": meta.get("lines", 0),
        }
        for path, meta in sorted(
            files.items(),
            key=lambda item: (
                -item[1].get("importance", 0),
                item[0],
            ),
        )[:30]
    ]

    return {
        "files": len(files),
        "languages": languages,
        "symbols": symbol_total,
        "imports": import_total,
        "important_files": important_files,
    }


def build_index(root: str | Path, force: bool = False) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    old = load_index(root)
    old_files = old.get("files", {})
    files: dict[str, Any] = {}
    stats = {
        "scanned": 0,
        "indexed": 0,
        "reused": 0,
        "changed": 0,
        "removed": 0,
        "errors": 0,
    }
    seen = set()

    for path in iter_indexable_files(root):
        stats["scanned"] += 1
        relative_path = str(path.relative_to(root))
        seen.add(relative_path)
        old_meta = old_files.get(relative_path, {})

        if not force and file_unchanged(path, old_meta):
            files[relative_path] = old_meta
            stats["reused"] += 1
            continue

        try:
            metadata = index_file(root, path)
        except Exception:
            stats["errors"] += 1
            continue

        metadata["version"] = INDEX_VERSION
        files[relative_path] = metadata
        stats["indexed"] += 1

        if relative_path in old_files:
            stats["changed"] += 1

    removed = sorted(set(old_files) - seen)
    stats["removed"] = len(removed)
    summary = summarize_index(files)
    data = {
        "version": INDEX_VERSION,
        "root": str(root),
        "generated_at": current_time(),
        "stats": stats,
        "summary": summary,
        "removed": removed[:200],
        "files": files,
    }
    save_index(root, data)
    return data


def get_index(root: str | Path) -> dict[str, Any]:
    return load_index(Path(root).expanduser().resolve())


def index_files(data: dict[str, Any]) -> dict[str, Any]:
    if "files" in data:
        return data.get("files", {})

    return data


def search_symbols_in_index(
    data: dict[str, Any],
    query: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    files = index_files(data)
    lowered = query.lower()
    matches = []

    for path, meta in files.items():
        for symbol in meta.get("symbols", []):
            name = symbol.get("name", "")

            if lowered not in name.lower():
                continue

            matches.append(
                {
                    "file": path,
                    "name": name,
                    "kind": symbol.get("kind", "symbol"),
                    "line": symbol.get("line", 1),
                    "language": meta.get("language", ""),
                    "importance": meta.get("importance", 0),
                }
            )

    return sorted(
        matches,
        key=lambda item: (-item.get("importance", 0), item["file"], item["line"]),
    )[:limit]


def changed_files(root: str | Path) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    data = load_index(root)
    files = index_files(data)
    changed = []
    missing = []

    for relative_path, meta in files.items():
        path = root / relative_path

        if not path.exists():
            missing.append(relative_path)
            continue

        try:
            stat = path.stat()
        except OSError:
            missing.append(relative_path)
            continue

        if meta.get("mtime_ns") != stat.st_mtime_ns or meta.get("size") != stat.st_size:
            changed.append(relative_path)

    return {
        "success": True,
        "changed": sorted(changed),
        "missing": sorted(missing),
        "total_changed": len(changed),
        "total_missing": len(missing),
        "index_path": str(index_path(root)),
    }


def ensure_fresh_index(root: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(root).expanduser().resolve()
    path = index_path(root)

    if not path.exists():
        data = build_index(root, force=False)
        return data, {
            "index_status": "built",
            "changed": [],
            "missing": [],
            "total_changed": 0,
            "total_missing": 0,
        }

    data = load_index(root)

    if data.get("version") != INDEX_VERSION or not index_files(data):
        data = build_index(root, force=False)
        return data, {
            "index_status": "rebuilt",
            "changed": [],
            "missing": [],
            "total_changed": 0,
            "total_missing": 0,
        }

    freshness = changed_files(root)

    if freshness.get("changed") or freshness.get("missing"):
        data = build_index(root, force=False)
        return data, {
            "index_status": "refreshed",
            "changed": freshness.get("changed", []),
            "missing": freshness.get("missing", []),
            "total_changed": freshness.get("total_changed", 0),
            "total_missing": freshness.get("total_missing", 0),
        }

    return data, {
        "index_status": "reused",
        "changed": [],
        "missing": [],
        "total_changed": 0,
        "total_missing": 0,
    }


def query_terms(query: str) -> list[str]:
    raw_terms = re.findall(r"[A-Za-z0-9_.$/-]+", query.lower())
    terms = []

    for term in raw_terms:
        term = term.strip("._/-$")

        if len(term) < 2:
            continue

        terms.append(term)

        for part in re.split(r"[_./-]+", term):
            if len(part) >= 3:
                terms.append(part)

    return sorted(set(terms), key=lambda value: (-len(value), value))


def camel_terms(query: str) -> list[str]:
    pieces = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+", query)
    return [piece.lower() for piece in pieces if len(piece) >= 2]


_WORD_RE = re.compile(r"[\w/.\-]+")


def _has_boundary_match(hay: str, term: str) -> bool:
    if term not in hay:
        return False

    for m in _WORD_RE.finditer(hay):
        tok = m.group(0)
        if term == tok or term in tok.split("_") or term in tok.split(".") or term in tok.split("/"):
            return True

    return False


def text_match_score(text: str, terms: list[str], exact_query: str) -> int:
    lowered = text.lower()
    score = 0

    if exact_query and exact_query in lowered:
        score += 40

    for term in terms:
        if _has_boundary_match(lowered, term):
            score += min(25, 4 + len(term))

    return score


def line_matches_terms(line: str, terms: list[str]) -> bool:
    lowered = line.lower()

    if not terms:
        return False

    if len(terms) == 1:
        return _has_boundary_match(lowered, terms[0])

    return all(_has_boundary_match(lowered, term) for term in terms)


def content_matches(root: Path, relative_path: str, terms: list[str]) -> list[dict[str, Any]]:
    path = root / relative_path

    try:
        if path.stat().st_size > MAX_CONTENT_SEARCH_BYTES:
            return []

        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    matches = []

    for line_number, line in enumerate(text.splitlines(), 1):
        if not line_matches_terms(line, terms):
            continue

        matches.append(
            {
                "line": line_number,
                "text": line.strip()[:240],
            }
        )

        if len(matches) >= MAX_CONTENT_MATCHES_PER_FILE:
            break

    return matches


def search_project_index(
    root: str | Path,
    data: dict[str, Any],
    query: str,
    limit: int = 20,
    include_content: bool = True,
) -> list[dict[str, Any]]:
    root = Path(root).expanduser().resolve()
    files = index_files(data)
    exact_query = query.lower().strip()
    terms = sorted(
        set(query_terms(query) + camel_terms(query)),
        key=lambda value: (-len(value), value),
    )
    primary_terms = [
        term
        for term in terms
        if len(term) >= 10 and ("_" in term or "." in term or "/" in term)
    ]

    if not terms and exact_query:
        terms = [exact_query]

    results = []

    for path, meta in files.items():
        score = 0
        reasons = []
        symbol_hits = []
        import_hits = []
        content_hits = []
        symbol_score_total = 0
        import_score_total = 0
        metadata_text = " ".join(
            [
                path,
                *[
                    symbol.get("name", "")
                    for symbol in meta.get("symbols", [])
                ],
                *meta.get("imports", []),
            ]
        ).lower()
        active_terms = terms

        if primary_terms and not any(term in metadata_text for term in primary_terms):
            active_terms = primary_terms

        path_score = text_match_score(path, active_terms, exact_query)
        if path_score:
            if exact_query and exact_query in path.lower():
                path_score += 80
            score += path_score + 20
            reasons.append("path")

        for symbol in meta.get("symbols", []):
            symbol_name = symbol.get("name", "")
            symbol_score = text_match_score(symbol_name, active_terms, exact_query)

            if not symbol_score:
                continue

            if exact_query and exact_query in symbol_name.lower():
                symbol_score += 140

            symbol_score_total += symbol_score + 35
            reasons.append("symbol")
            symbol_hits.append(symbol)

        for imported in meta.get("imports", []):
            import_score = text_match_score(imported, active_terms, exact_query)

            if not import_score:
                continue

            import_score_total += import_score + 15
            reasons.append("import")
            import_hits.append(imported)

        score += min(260, symbol_score_total)
        score += min(120, import_score_total)

        important_score = meta.get("importance", 0)
        if important_score and score:
            score += min(30, important_score // 3)
            reasons.append("important")

        if include_content and active_terms:
            content_hits = content_matches(root, path, active_terms)

            if content_hits:
                score += min(45, len(content_hits) * 15)
                reasons.append("content")

        if score <= 0:
            continue

        results.append(
            {
                "file": path,
                "score": score,
                "language": meta.get("language", ""),
                "lines": meta.get("lines", 0),
                "importance": meta.get("importance", 0),
                "reasons": sorted(set(reasons)),
                "symbols": symbol_hits[:8],
                "imports": import_hits[:8],
                "content_matches": content_hits,
            }
        )

    return sorted(
        results,
        key=lambda item: (-item["score"], -item.get("importance", 0), item["file"]),
    )[:limit]


# ------------------------------------------------------------------
# Reference-path indexing helpers (read-only, cached outside refs)
# ------------------------------------------------------------------

REF_INDEX_ROOT = Path.home() / ".rectury" / "references"


def reference_cache_dir(reference: str | Path) -> Path:
    ref = Path(reference).expanduser().resolve()
    digest = hashlib.sha256(str(ref).encode("utf-8")).hexdigest()[:16]
    return REF_INDEX_ROOT / digest


def reference_index_path(reference: str | Path) -> Path:
    return reference_cache_dir(reference) / "index.json"


def load_reference_index(reference: str | Path) -> dict[str, Any]:
    ref = Path(reference).expanduser().resolve()

    try:
        data = json.loads(reference_index_path(ref).read_text(encoding="utf-8"))
    except Exception:
        return empty_index(ref)

    if isinstance(data, dict) and "files" in data:
        return data

    return empty_index(ref)


def save_reference_index(reference: str | Path, data: dict[str, Any]) -> None:
    path = reference_index_path(reference)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_reference_index(reference: str | Path, force: bool = False) -> dict[str, Any]:
    ref = Path(reference).expanduser().resolve()
    old = load_reference_index(ref)
    old_files = old.get("files", {})
    files: dict[str, Any] = {}
    stats = {
        "scanned": 0,
        "indexed": 0,
        "reused": 0,
        "changed": 0,
        "removed": 0,
        "errors": 0,
    }
    seen = set()

    for path in iter_indexable_files(ref):
        stats["scanned"] += 1
        relative_path = str(path.relative_to(ref))
        seen.add(relative_path)
        old_meta = old_files.get(relative_path, {})

        if not force and file_unchanged(path, old_meta):
            files[relative_path] = old_meta
            stats["reused"] += 1
            continue

        try:
            metadata = index_file(ref, path)
        except Exception:
            stats["errors"] += 1
            continue

        metadata["version"] = INDEX_VERSION
        files[relative_path] = metadata
        stats["indexed"] += 1

        if relative_path in old_files:
            stats["changed"] += 1

    removed = sorted(set(old_files) - seen)
    stats["removed"] = len(removed)
    data = {
        "version": INDEX_VERSION,
        "root": str(ref),
        "generated_at": current_time(),
        "stats": stats,
        "summary": summarize_index(files),
        "removed": removed[:200],
        "files": files,
    }
    save_reference_index(ref, data)
    return data


def changed_reference_files(reference: str | Path) -> dict[str, Any]:
    ref = Path(reference).expanduser().resolve()
    data = load_reference_index(ref)
    files = index_files(data)
    changed = []
    missing = []

    for relative_path, meta in files.items():
        path = ref / relative_path

        if not path.exists():
            missing.append(relative_path)
            continue

        try:
            stat = path.stat()
        except OSError:
            missing.append(relative_path)
            continue

        if meta.get("mtime_ns") != stat.st_mtime_ns or meta.get("size") != stat.st_size:
            changed.append(relative_path)

    return {
        "success": True,
        "changed": sorted(changed),
        "missing": sorted(missing),
        "total_changed": len(changed),
        "total_missing": len(missing),
        "index_path": str(reference_index_path(ref)),
    }


def ensure_fresh_reference_index(reference: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    ref = Path(reference).expanduser().resolve()
    path = reference_index_path(ref)

    if not path.exists():
        data = build_reference_index(ref, force=False)
        return data, {
            "index_status": "built",
            "changed": [],
            "missing": [],
            "total_changed": 0,
            "total_missing": 0,
        }

    data = load_reference_index(ref)

    if (
        data.get("version") != INDEX_VERSION
        or not index_files(data)
        or not data.get("summary")
    ):
        data = build_reference_index(ref, force=False)
        return data, {
            "index_status": "rebuilt",
            "changed": [],
            "missing": [],
            "total_changed": 0,
            "total_missing": 0,
        }

    freshness = changed_reference_files(ref)

    if freshness.get("changed") or freshness.get("missing"):
        data = build_reference_index(ref, force=False)
        return data, {
            "index_status": "refreshed",
            "changed": freshness.get("changed", []),
            "missing": freshness.get("missing", []),
            "total_changed": freshness.get("total_changed", 0),
            "total_missing": freshness.get("total_missing", 0),
        }

    return data, {
        "index_status": "reused",
        "changed": [],
        "missing": [],
        "total_changed": 0,
        "total_missing": 0,
    }


def reference_index_summary(
    reference: Path,
    data: dict[str, Any],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    summary = data.get("summary") or summarize_index(index_files(data))
    stats = data.get("stats", {})

    return {
        "success": True,
        "reference": str(reference),
        "index_path": str(reference_index_path(reference)),
        "index_status": freshness.get("index_status", "unknown"),
        "files_indexed": summary.get("files", len(index_files(data))),
        "languages": summary.get("languages", {}),
        "symbols": summary.get("symbols", 0),
        "imports": summary.get("imports", 0),
        "important_files": summary.get("important_files", []),
        "stats": stats,
        "changed": freshness.get("changed", []),
        "missing": freshness.get("missing", []),
        "total_changed": freshness.get("total_changed", 0),
        "total_missing": freshness.get("total_missing", 0),
    }


def index_reference(reference: str | Path, force: bool = False) -> dict[str, Any]:
    ref = Path(reference).expanduser().resolve()

    if force:
        data = build_reference_index(ref, force=True)
        freshness = {
            "index_status": "rebuilt",
            "changed": [],
            "missing": [],
            "total_changed": 0,
            "total_missing": 0,
        }
    else:
        data, freshness = ensure_fresh_reference_index(ref)

    return reference_index_summary(ref, data, freshness)


def reference_overview(reference: str | Path) -> dict[str, Any]:
    ref = Path(reference).expanduser().resolve()
    data, freshness = ensure_fresh_reference_index(ref)
    return reference_index_summary(ref, data, freshness)


def search_reference_project(
    query: str,
    reference: str | Path,
    limit: int = 20,
    include_content: bool = True,
) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        return {"error": "query must be a non-empty string."}

    ref = Path(reference).expanduser().resolve()
    data, freshness = ensure_fresh_reference_index(ref)
    results = search_project_index(
        ref,
        data,
        query,
        limit=limit,
        include_content=include_content,
    )

    return {
        "success": True,
        "query": query,
        "reference": str(ref),
        "index_path": str(reference_index_path(ref)),
        "index_status": freshness.get("index_status", "unknown"),
        "total": len(results),
        "results": results,
    }
