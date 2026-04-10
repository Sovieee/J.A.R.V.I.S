conversation_history = []

def add_to_history(role, message):
    conversation_history.append({
        "role": role,
        "message": message
    })

    if len(conversation_history) > 6:
        conversation_history.pop(0)