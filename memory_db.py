import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langgraph.store.memory import InMemoryStore

load_dotenv()

MEMORY_DB = Path("memories.db")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=1536,
)

store = InMemoryStore(index={"embed": embeddings, "dims": 1536})

_store_initialized = False


def init_memory_db() -> None:
    """Initialize SQLite and index existing facts for semantic search."""
    global _store_initialized

    with sqlite3.connect(MEMORY_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                fact TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if _store_initialized:
            return

        rows = conn.execute("SELECT id, user_id, fact FROM memories").fetchall()

    for memory_id, user_id, fact in rows:
        store.put(
            ("memories", user_id),
            str(memory_id),
            {"fact": fact},
        )

    _store_initialized = True


def save_memory(user_id: str, fact: str) -> None:
    """Save a fact to SQLite and index it for semantic retrieval."""
    init_memory_db()

    with sqlite3.connect(MEMORY_DB) as conn:
        existing = conn.execute(
            """
            SELECT id FROM memories
            WHERE user_id = ? AND fact = ?
            """,
            (user_id, fact),
        ).fetchone()

        if existing is not None:
            memory_id = existing[0]
        else:
            cursor = conn.execute(
                """
                INSERT INTO memories (user_id, fact)
                VALUES (?, ?)
                """,
                (user_id, fact),
            )
            memory_id = cursor.lastrowid

    store.put(
        ("memories", user_id),
        str(memory_id),
        {"fact": fact},
    )


def get_memories(user_id: str) -> list[str]:
    """Return all saved facts for the sidebar."""
    init_memory_db()

    with sqlite3.connect(MEMORY_DB) as conn:
        rows = conn.execute(
            """
            SELECT fact FROM memories
            WHERE user_id = ?
            ORDER BY created_at, id
            """,
            (user_id,),
        ).fetchall()

    return [row[0] for row in rows]


def search_memories(
    user_id: str,
    query: str,
    limit: int = 5,
) -> list[str]:
    """Retrieve facts relevant to a user's message."""
    init_memory_db()

    results = store.search(
        ("memories", user_id),
        query=query,
        limit=limit,
    )

    return [item.value["fact"] for item in results]


def delete_memory(user_id: str, fact: str) -> bool:
    """Delete a fact from persistent storage and semantic search."""
    init_memory_db()

    with sqlite3.connect(MEMORY_DB) as conn:
        row = conn.execute(
            """
            SELECT id FROM memories
            WHERE user_id = ? AND fact = ?
            ORDER BY id
            LIMIT 1
            """,
            (user_id, fact),
        ).fetchone()

        if row is None:
            return False

        memory_id = row[0]

        conn.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,),
        )

    store.delete(
        ("memories", user_id),
        str(memory_id),
    )

    return True
