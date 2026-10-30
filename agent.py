import os
import sqlite3

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import SecretStr

from memory_db import search_memories
from prompts.system_prompt import SYSTEM_PROMPT
from prompts.thread_summary_prompt import THREAD_SUMMARY_PROMPT

load_dotenv()


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
    )


# Persistent conversation history.
_THREADS_CONN = sqlite3.connect(
    "threads.db",
    check_same_thread=False,
)
_CHECKPOINTER = SqliteSaver(_THREADS_CONN)
_CHECKPOINTER.setup()


def _init_thread_titles() -> None:
    """Create persistent storage for conversation titles."""
    with _THREADS_CONN:
        _THREADS_CONN.execute(
            """
            CREATE TABLE IF NOT EXISTS thread_titles (
                thread_id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            )
            """
        )


def _make_remember_tool(pending_memories: list[str]):
    """Propose facts without saving them automatically."""

    @tool
    def remember(fact: str) -> str:
        """Propose a personal fact for user confirmation."""
        fact = fact.strip()

        if fact and fact not in pending_memories:
            pending_memories.append(fact)

        return (
            "The fact is pending user confirmation and has not been saved. "
            "Continue responding naturally and tell the user they can "
            "confirm or cancel the proposed memory in the application."
        )

    return remember


def build_agent(
    user_id: str,
    user_message: str,
    pending_memories: list[str] | None = None,
):
    """Build an agent with memories relevant to the current message."""
    if pending_memories is None:
        pending_memories = []

    memories = search_memories(
        user_id=user_id,
        query=user_message,
        limit=5,
    )

    memory_bullets = (
        "\n".join(f"- {fact}" for fact in memories)
        if memories
        else "(no relevant memories found)"
    )

    system_prompt = SYSTEM_PROMPT.format(
        memory_bullets=memory_bullets,
    )

    return create_agent(
        model=_build_llm(),
        tools=[_make_remember_tool(pending_memories)],
        system_prompt=system_prompt,
        checkpointer=_CHECKPOINTER,
    )


def summarise_thread(thread_id: str) -> str:
    """Generate and persist a concise conversation title."""
    _init_thread_titles()

    saved_title = _THREADS_CONN.execute(
        "SELECT title FROM thread_titles WHERE thread_id = ?",
        (thread_id,),
    ).fetchone()

    if saved_title:
        return saved_title[0]

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpoint_tuple = _CHECKPOINTER.get_tuple(config)

    if checkpoint_tuple is None:
        return "New conversation"

    messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])

    conversation_parts = []

    for message in messages:
        role = getattr(message, "type", "")
        content = getattr(message, "content", "")

        if role not in ("human", "ai"):
            continue

        if not isinstance(content, str) or not content.strip():
            continue

        label = "User" if role == "human" else "Assistant"
        conversation_parts.append(f"{label}: {content}")

    if not conversation_parts:
        return "New conversation"

    conversation = "\n".join(conversation_parts)

    response = _build_llm().invoke(
        THREAD_SUMMARY_PROMPT.format(conversation=conversation)
    )

    title = str(response.content).strip().strip('"').strip("'")
    title = title or "Untitled conversation"

    with _THREADS_CONN:
        _THREADS_CONN.execute(
            """
            INSERT OR REPLACE INTO thread_titles (thread_id, title)
            VALUES (?, ?)
            """,
            (thread_id, title),
        )

    return title


def list_thread_ids(limit: int = 10) -> list[str]:
    """Return the most recently updated conversation threads."""
    rows = _THREADS_CONN.execute(
        """
        SELECT thread_id, MAX(rowid) AS latest
        FROM checkpoints
        WHERE checkpoint_ns = ''
        GROUP BY thread_id
        ORDER BY latest DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [row[0] for row in rows]


def load_thread_messages(thread_id: str) -> list[dict[str, str]]:
    """Load displayable messages when reopening a conversation."""
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpoint_tuple = _CHECKPOINTER.get_tuple(config)

    if checkpoint_tuple is None:
        return []

    messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])

    history = []

    for message in messages:
        role = getattr(message, "type", "")
        content = getattr(message, "content", "")

        if role == "human":
            display_role = "user"
        elif role == "ai":
            display_role = "assistant"
        else:
            continue

        if isinstance(content, str) and content.strip():
            history.append({"role": display_role, "content": content})

    return history
