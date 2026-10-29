import sqlite3
from pathlib import Path

MEMORY_DB = Path("memories.db")


def init_memory_db() -> None:
    """Create the memories table if it does not already exist."""
    with sqlite3.connect(MEMORY_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL,
                fact       TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )



def save_memory(user_id: str, fact: str) -> None:
    with sqlite3.connect(MEMORY_DB) as conn:
        existing = conn.execute(
            "SELECT 1 FROM memories WHERE user_id = ? AND fact = ?",
            (user_id, fact),
        ).fetchone()

        if existing is None:
            conn.execute(
                "INSERT INTO memories (user_id, fact) VALUES (?, ?)",
                (user_id, fact),
            )



def get_memories(user_id: str) -> list[str]:
    with sqlite3.connect(MEMORY_DB) as conn:
        rows = conn.execute(
            "SELECT fact FROM memories WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()
    return [row[0] for row in rows]
