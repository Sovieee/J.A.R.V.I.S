# 🔹 Global state
conversation_mode = False
pending_intent = None


# ------------------------
# 🔹 Conversation Mode
# ------------------------

def set_conversation_mode(value: bool):
    global conversation_mode
    conversation_mode = value


def get_conversation_mode():
    global conversation_mode
    return conversation_mode


# ------------------------
# 🔹 Pending Intent
# ------------------------

def set_pending_intent(intent):
    global pending_intent
    pending_intent = intent


def get_pending_intent():
    global pending_intent
    return pending_intent


def clear_pending_intent():
    global pending_intent
    pending_intent = None