conversation_history = []

def add_to_history(role, message):
    conversation_history.append({
        "role": role,
        "message": message
    })

    # keep only last 6 messages (to avoid overload)
    if len(conversation_history) > 6:
        conversation_history.pop(0)


def get_context():
    context = ""
    for entry in conversation_history:
        context += f"{entry['role']}: {entry['message']}\n"
    return context