from uuid import uuid4

import streamlit as st
from langchain_core.runnables import RunnableConfig

from agent import (
    build_agent,
    list_thread_ids,
    load_thread_messages,
    summarise_thread,
)
from memory_db import delete_memory, get_memories, save_memory

st.set_page_config(page_title="Memory Chat", page_icon="🧠")

# --- Initialize session state ---
if "pending_memories" not in st.session_state:
    st.session_state.pending_memories = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())

if "thread_titles" not in st.session_state:
    st.session_state.thread_titles = {}

if "user_id" not in st.session_state:
    st.session_state.user_id = None

# --- Sidebar ---
with st.sidebar:
    st.header("Session")
    user_id = st.text_input("User ID", value="alice")

    # Start a separate active thread when the user changes.
    if st.session_state.user_id != user_id:
        st.session_state.user_id = user_id
        st.session_state.thread_id = str(uuid4())
        st.session_state.messages = []
        st.session_state.pending_memories = []

    if st.button("Start a new chat", use_container_width=True):
        st.session_state.thread_id = str(uuid4())
        st.session_state.messages = []
        st.session_state.pending_memories = []
        st.rerun()

    current_thread_id = st.session_state.thread_id
    st.caption(f"Current thread ID: `{current_thread_id[:8]}...`")

    # --- Recent conversations ---
    st.subheader("Recent conversations")

    thread_ids = list_thread_ids(limit=10)

    if not thread_ids:
        st.caption("Your conversations will appear here.")

    for thread_id in thread_ids:
        if thread_id not in st.session_state.thread_titles:
            st.session_state.thread_titles[thread_id] = summarise_thread(thread_id)

        title = st.session_state.thread_titles[thread_id]
        is_current = thread_id == current_thread_id

        if st.button(
            f"{'📍 ' if is_current else ''}{title}",
            key=f"open_thread_{thread_id}",
            use_container_width=True,
            disabled=is_current,
        ):
            st.session_state.thread_id = thread_id
            st.session_state.messages = load_thread_messages(thread_id)
            st.session_state.pending_memories = []
            st.rerun()

    # --- Long-term memory and Forget buttons ---
    st.header("Long-term memory")
    memories = get_memories(user_id)

    if memories:
        for index, fact in enumerate(memories):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(fact)

            with col2:
                if st.button(
                    "Forget",
                    key=f"forget_memory_{user_id}_{index}",
                    help="Delete this saved fact",
                ):
                    if delete_memory(user_id, fact):
                        st.toast("Memory forgotten.")
                    else:
                        st.warning("That memory was not found.")

                    st.rerun()
    else:
        st.write("_No memories yet._")

# --- Main chat ---
st.title("🧠 Memory Chat")
st.caption(
    "Share something worth remembering. You decide which facts "
    "are saved for future conversations."
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Memory confirmation ---
if st.session_state.pending_memories:
    st.subheader("Should I remember this?")

    for index, fact in enumerate(st.session_state.pending_memories):
        with st.container(border=True):
            st.write(f"**Proposed memory:** {fact}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Confirm",
                    key=f"confirm_memory_{index}",
                    use_container_width=True,
                ):
                    save_memory(user_id, fact)
                    st.session_state.pending_memories.pop(index)
                    st.success("Memory saved.")
                    st.rerun()

            with col2:
                if st.button(
                    "Cancel",
                    key=f"cancel_memory_{index}",
                    use_container_width=True,
                ):
                    st.session_state.pending_memories.pop(index)
                    st.info("Memory discarded.")
                    st.rerun()

# --- Process new messages ---
if user_input := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    agent = build_agent(
        user_id,
        user_input,
        pending_memories=st.session_state.pending_memories,
    )

    config: RunnableConfig = {"configurable": {"thread_id": st.session_state.thread_id}}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config=config,
    )

    reply = result["messages"][-1].content

    if not isinstance(reply, str):
        reply = str(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    st.session_state.thread_titles.pop(st.session_state.thread_id, None)

    st.rerun()
