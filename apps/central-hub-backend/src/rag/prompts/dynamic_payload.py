"""Layer 5: Dynamic Payload Injection (Chunks, Chat History, User Query)."""

from typing import List, Dict, Any, Optional

def get_dynamic_payload(
    retrieved_chunks: str,
    chat_history: Optional[List[Dict[str, Any]]],
    user_query: str,
    max_history_turns: int = 3
) -> str:
    """
    Assembles the dynamic variables block.
    Slices chat history to the configured maximum turns and places the user query at the very end.
    """
    # 1. Retrieved Context Block
    context_block = (
        "==============================\n"
        "RETRIEVED CONTEXT\n"
        "==============================\n"
        f"{retrieved_chunks.strip()}\n\n"
    )

    # 2. Chat History Block (Bounded to prevent token bloating)
    history_str = ""
    if chat_history:
        # A conversation turn consists of a user message and a bot reply (max_history_turns * 2 items)
        max_messages = max_history_turns * 2
        sliced_history = chat_history[-max_messages:]
        
        history_lines = []
        for msg in sliced_history:
            role = str(msg.get("role", "user")).capitalize()
            content = str(msg.get("content", "")).strip()
            history_lines.append(f"{role}: {content}")
        
        history_str = "\n".join(history_lines)

    history_block = (
        "==============================\n"
        "RECENT CHAT HISTORY\n"
        "==============================\n"
        f"{history_str.strip() if history_str else '[No previous conversation history]'}\n\n"
    )

    # 3. User Question Block (Always the final element of the prompt)
    question_block = (
        "==============================\n"
        "USER QUESTION\n"
        "==============================\n"
        f"{user_query.strip()}\n"
    )

    return f"{context_block}{history_block}{question_block}"
