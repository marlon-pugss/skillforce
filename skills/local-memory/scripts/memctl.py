#!/usr/bin/env python3
"""Local, project-scoped conversation memory backed by SQLite FTS5."""

from __future__ import annotations

import argparse
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = ".memory"
CONVERSATIONS_DIR = "conversations"
DATABASE_NAME = "index.db"
VALID_OUTCOMES = ("code", "decision", "research", "blocked")


def memory_paths(root: Path) -> tuple[Path, Path]:
    memory_dir = root.resolve() / MEMORY_DIR
    return memory_dir / CONVERSATIONS_DIR, memory_dir / DATABASE_NAME


def connect(database: Path) -> sqlite3.Connection:
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            tags TEXT NOT NULL,
            summary TEXT NOT NULL,
            outcome TEXT NOT NULL,
            created_at TEXT NOT NULL,
            body TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
            title, tags, summary, body, content='conversations', content_rowid='id'
        );
        CREATE TRIGGER IF NOT EXISTS conversations_ai AFTER INSERT ON conversations BEGIN
            INSERT INTO conversations_fts(rowid, title, tags, summary, body)
            VALUES (new.id, new.title, new.tags, new.summary, new.body);
        END;
        CREATE TRIGGER IF NOT EXISTS conversations_ad AFTER DELETE ON conversations BEGIN
            INSERT INTO conversations_fts(conversations_fts, rowid, title, tags, summary, body)
            VALUES ('delete', old.id, old.title, old.tags, old.summary, old.body);
        END;
        CREATE TRIGGER IF NOT EXISTS conversations_au AFTER UPDATE ON conversations BEGIN
            INSERT INTO conversations_fts(conversations_fts, rowid, title, tags, summary, body)
            VALUES ('delete', old.id, old.title, old.tags, old.summary, old.body);
            INSERT INTO conversations_fts(rowid, title, tags, summary, body)
            VALUES (new.id, new.title, new.tags, new.summary, new.body);
        END;
        """
    )
    return connection


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "conversation"


def upsert(connection: sqlite3.Connection, path: Path, metadata: dict[str, str], body: str) -> int:
    cursor = connection.execute(
        """
        INSERT INTO conversations(path, title, source, tags, summary, outcome, created_at, body)
        VALUES (:path, :title, :source, :tags, :summary, :outcome, :created_at, :body)
        ON CONFLICT(path) DO UPDATE SET
            title=excluded.title, source=excluded.source, tags=excluded.tags,
            summary=excluded.summary, outcome=excluded.outcome,
            created_at=excluded.created_at, body=excluded.body
        RETURNING id
        """,
        {**metadata, "path": str(path), "body": body},
    )
    conversation_id = int(cursor.fetchone()[0])
    connection.commit()
    return conversation_id


def render_document(metadata: dict[str, str], body: str) -> str:
    header = "\n".join(f"{key}: {metadata[key]}" for key in ("title", "source", "tags", "summary", "outcome", "created_at"))
    return f"---\n{header}\n---\n\n{body.rstrip()}\n"


def parse_document(content: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", content, re.DOTALL)
    if not match:
        raise ValueError("conversation file is missing YAML-style front matter")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    required = {"title", "source", "tags", "summary", "outcome", "created_at"}
    missing = required - metadata.keys()
    if missing:
        raise ValueError(f"missing metadata: {', '.join(sorted(missing))}")
    return metadata, match.group(2).rstrip() + "\n"


def save(args: argparse.Namespace) -> None:
    root = Path(args.root)
    conversations, database = memory_paths(root)
    conversations.mkdir(parents=True, exist_ok=True)
    body = Path(args.file).read_text(encoding="utf-8")
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metadata = {
        "title": args.title,
        "source": args.source,
        "tags": args.tags,
        "summary": args.summary,
        "outcome": args.outcome,
        "created_at": created_at,
    }
    filename = f"{created_at[:10]}_{slugify(args.title)}.md"
    path = conversations / filename
    suffix = 2
    while path.exists():
        path = conversations / f"{created_at[:10]}_{slugify(args.title)}-{suffix}.md"
        suffix += 1
    path.write_text(render_document(metadata, body), encoding="utf-8")
    with connect(database) as connection:
        conversation_id = upsert(connection, path.relative_to(root.resolve()), metadata, body)
    print(f"saved {conversation_id}: {path}")


def search(args: argparse.Namespace) -> None:
    _, database = memory_paths(Path(args.root))
    if not database.exists():
        print("no results")
        return
    with connect(database) as connection:
        rows = connection.execute(
            """
            SELECT c.id, c.title, c.summary, c.created_at,
                   snippet(conversations_fts, 3, '[', ']', ' … ', 20) AS excerpt
            FROM conversations_fts
            JOIN conversations c ON c.id = conversations_fts.rowid
            WHERE conversations_fts MATCH ?
            ORDER BY rank LIMIT ?
            """,
            (args.query, args.limit),
        ).fetchall()
    if not rows:
        print("no results")
    for row in rows:
        print(f"{row['id']} | {row['created_at'][:10]} | {row['title']}\n  {row['summary']}\n  {row['excerpt']}")


def show(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    _, database = memory_paths(root)
    if not database.exists():
        raise SystemExit(f"conversation {args.id} not found")
    with connect(database) as connection:
        row = connection.execute("SELECT path FROM conversations WHERE id = ?", (args.id,)).fetchone()
    if row is None:
        raise SystemExit(f"conversation {args.id} not found")
    print((root / row["path"]).read_text(encoding="utf-8"), end="")


def list_conversations(args: argparse.Namespace) -> None:
    _, database = memory_paths(Path(args.root))
    if not database.exists():
        print("no conversations")
        return
    with connect(database) as connection:
        rows = connection.execute(
            "SELECT id, title, source, outcome, created_at FROM conversations ORDER BY created_at DESC, id DESC LIMIT ?",
            (args.limit,),
        ).fetchall()
    if not rows:
        print("no conversations")
    for row in rows:
        print(f"{row['id']} | {row['created_at'][:10]} | {row['title']} | {row['source']} | {row['outcome']}")


def reindex(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    conversations, database = memory_paths(root)
    with connect(database) as connection:
        connection.execute("DELETE FROM conversations")
        indexed = 0
        for path in sorted(conversations.glob("*.md")):
            try:
                metadata, body = parse_document(path.read_text(encoding="utf-8"))
                upsert(connection, path.relative_to(root), metadata, body)
                indexed += 1
            except ValueError as error:
                print(f"skipped {path}: {error}")
    print(f"indexed {indexed} conversation(s)")


def parser() -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(description=__doc__)
    root_parser.add_argument("--root", default=".", help="project root (default: current directory)")
    commands = root_parser.add_subparsers(dest="command", required=True)

    save_parser = commands.add_parser("save", help="save and index a conversation")
    save_parser.add_argument("--title", required=True)
    save_parser.add_argument("--source", required=True)
    save_parser.add_argument("--tags", default="")
    save_parser.add_argument("--summary", required=True)
    save_parser.add_argument("--outcome", choices=VALID_OUTCOMES, required=True)
    save_parser.add_argument("--file", required=True, help="Markdown conversation body")
    save_parser.set_defaults(handler=save)

    search_parser = commands.add_parser("search", help="full-text search conversations")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.set_defaults(handler=search)

    show_parser = commands.add_parser("show", help="show a conversation by ID")
    show_parser.add_argument("id", type=int)
    show_parser.set_defaults(handler=show)

    list_parser = commands.add_parser("list", help="list recent conversations")
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.set_defaults(handler=list_conversations)

    reindex_parser = commands.add_parser("reindex", help="rebuild the index from Markdown files")
    reindex_parser.set_defaults(handler=reindex)
    return root_parser


def main() -> None:
    args = parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
