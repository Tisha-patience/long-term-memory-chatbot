THREAD_SUMMARY_PROMPT = """
Create a short, descriptive title for this conversation.

Requirements:
- Use 3 to 7 words.
- Capture the main topic of the conversation.
- Make the title specific and easy to recognize in a conversation list.
- Return only the title, without quotation marks or explanation.

Conversation:
{conversation}
"""
