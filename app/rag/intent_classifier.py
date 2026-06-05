import re

METADATA_KEYWORDS = [
    "file",
    "files",
    "document",
    "documents",
    "uploaded",
    "upload",
    "pdf",
    "how many files",
    "how many documents",
    "which files",
    "list files",
    "list documents",
    "show files",
    "show documents"
]

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "hii",
    "yo"
}


def classify_intent(query: str) -> str:

    question = query.lower().strip()
    print("CLASSIFYING INTENT FOR:", question)
    # Greeting intent
    if question in GREETINGS:
        print("INTENT: greeting")
        return "greeting"

    # Metadata intent
    for keyword in METADATA_KEYWORDS:

        if keyword in question:

            return "metadata"

    # Default
    return "knowledge"