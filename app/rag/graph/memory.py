conversation_memory = {}


def get_memory(session_id: str):

    return conversation_memory.get(
        session_id,
        []
    )


def add_to_memory(
    session_id: str,
    role: str,
    content: str
):

    if session_id not in conversation_memory:

        conversation_memory[session_id] = []

    conversation_memory[session_id].append({

        "role": role,
        "content": content

    })


def build_chat_history(session_id: str):

    memory = get_memory(session_id)

    return "\n".join([

        f"{item['role']}: {item['content']}"

        for item in memory[-6:]

    ])