conversation_context = {}


def get_context(session_id):

    return conversation_context.get(
        session_id,
        {}
    )


def update_context(
    session_id,
    entity=None,
    company=None,
    document=None
):

    if session_id not in conversation_context:

        conversation_context[session_id] = {}

    if entity:

        conversation_context[
            session_id
        ]["entity"] = entity

    if company:

        conversation_context[
            session_id
        ]["company"] = company

    if document:

        conversation_context[
            session_id
        ]["document"] = document