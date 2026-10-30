# Long-Term Memory Chatbot

An AI-powered chatbot that remembers useful information about users across conversations. Instead of treating every conversation as a fresh interaction, it uses persistent memory, semantic retrieval, and conversation history to provide more personalized responses.

Built with **Python, Streamlit, LangChain, LangGraph, SQLite, and OpenAI** as part of my AI Engineering learning journey at Turing College.

## Features

### 1. Persistent User Memory
- Stores useful facts shared by users.
- Keeps memories across different conversations.
- Separates memories by user ID.

### 2. Semantic Memory Retrieval
- Uses OpenAI embeddings (`text-embedding-3-small`) to create vector representations of memories.
- Retrieves relevant memories based on the current conversation.
- Avoids adding every stored memory to the prompt.

### 3. Human-in-the-Loop Memory Management
- Allows the AI to propose information worth remembering.
- Users can review proposed memories.
- Users explicitly confirm or cancel before a memory is saved.

### 4. Conversation History
- Maintains conversation state using LangGraph's SQLite checkpointer.
- Generates short summaries for conversations.
- Allows users to revisit previous conversations.

### 5. Memory Management
- Displays saved memories in the interface.
- Allows users to delete memories they no longer want stored.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Chat interface |
| LangChain | Agent creation and tool integration |
| LangGraph | Agent execution, state and persistence |
| OpenAI GPT-4.1 mini | Language model |
| OpenAI text-embedding-3-small | Memory embeddings |
| SQLite | Persistent memory and conversation checkpoints |

## Project Structure

```text
long-term-memory-chabot/
│
├── app.py
├── agent.py
├── memory_db.py
├── prompts/
│   ├── __init__.py
│   ├── system_prompt.py
│   └── thread_summary_prompt.py
│
├── memories.db
├── threads.db
├── .env
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/Tisha-patience/long-term-memory-chabot.git
cd long-term-memory-chabot
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
```

Replace the placeholder with your own OpenAI API key.

### 4. Run the application

```bash
uv run streamlit run app.py
```

Streamlit will provide a local URL where you can access the chatbot in your browser.

## How It Works

1. A user starts a conversation with the chatbot.
2. The agent retrieves relevant memories using semantic search.
3. Retrieved memories are included in the agent's context.
4. The agent generates a response using the current conversation and relevant user information.
5. When useful new information is identified, the agent proposes it as a memory.
6. The user reviews and confirms the proposed memory before it is saved.
7. Confirmed memories are stored in SQLite and indexed for semantic retrieval.
8. Conversation checkpoints and summaries allow users to return to previous conversations.

## Learning Outcomes

This project provided practical experience with:

- Building AI agents using LangChain and LangGraph.
- Implementing long-term memory for conversational AI.
- Understanding embeddings and semantic search.
- Managing persistent state with SQLite.
- Implementing human-in-the-loop workflows.
- Separating prompt templates from application logic.
- Managing conversation threads and summaries.

