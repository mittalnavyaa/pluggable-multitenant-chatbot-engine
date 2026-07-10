"""Layer 4: Graceful Fallback Mechanics."""

def get_fallback_rules(configured_fallback: str) -> str:
    """
    Constructs fallback instructions defining the exact message string to return
    when context validation fails.
    """
    fallback_message = (
        "==============================\n"
        "FALLBACK INSTRUCTIONS\n"
        "==============================\n"
        "If the retrieved documentation is empty or does not provide the explicit answer to the user's question, "
        "you must output the following fallback message exactly. Do not add explanations, apologies, or conversational filler:\n\n"
        f"\"{configured_fallback.strip()}\"\n"
    )
    return fallback_message
