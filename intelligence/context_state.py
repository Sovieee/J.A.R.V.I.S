state = {
    "pending_intent": None
}


def set_pending_intent(intent):
    state["pending_intent"] = intent


def get_pending_intent():
    return state.get("pending_intent")


def clear_pending_intent():
    state["pending_intent"] = None