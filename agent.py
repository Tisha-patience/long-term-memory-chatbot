import os
import sqlite3

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

load_dotenv()
from langgraph.checkpoint.sqlite import SqliteSaver

from memory_db import get_memories, save_memory


def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=SecretStr(os.environ["OPENAI_API_KEY"]),
    )


# One shared connection for the checkpointer, reused across requests
_THREADS_CONN = sqlite3.connect("threads.db", check_same_thread=False)
_CHECKPOINTER = SqliteSaver(_THREADS_CONN)
_CHECKPOINTER.setup()


def _make_remember_tool(user_id: str):
    """Factory that binds the current user_id into the tool via a closure."""

    @tool
    def remember(fact: str) -> str:
        """Save a personal fact about the user to long-term memory.

        Call this whenever the user tells you something worth keeping
        between conversations (food preferences, location, goals, name,
        allergies, and so on).
        """
        save_memory(user_id, fact)
        return f"Saved to long-term memory: {fact}"

    return remember


def build_agent(user_id: str):
    """Return a fresh agent with the current user's memories loaded into its prompt."""
    memories = get_memories(user_id)
    memory_bullets = "\n".join(f"- {m}" for m in memories) or "(nothing yet)"

    system_prompt = (
        "You are a helpful assistant with long-term memory.\n\n"
        f"What you remember about this user:\n{memory_bullets}\n\n"
        "IMPORTANT: You have no persistent memory of your own — your context "
        "window is erased between sessions. Whenever the user tells you "
        "anything personal (preferences, dietary needs, location, goals, name, "
        "allergies, or any fact they want recalled later), you MUST call the "
        "`remember` tool immediately. Do not say 'I'll remember that' without "
        "calling the tool; saying it does not save anything."

        "Use the saved memories above when answering the user's questions. "
        "Personalize recommendations using relevant preferences and "
        "dietary restrictions already stored. Do not ask the user to repeat "
        "information that is already available in memory. For food "
        "recommendations, always respect any saved allergies and dietary "
        "preferences.\n\n"

    )

    return create_agent(
        model=_build_llm(),
        tools=[_make_remember_tool(user_id)],
        system_prompt=system_prompt,
        checkpointer=_CHECKPOINTER,
    )
