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
    "show documents",
    "list all files",
    "list all documents",   
    "list all uploaded files",
    "list all uploaded documents",
    "list all docs"
]

GREETINGS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "how are you",
    "i am good",
    "im good",
    "it was good",
    "good",
    "great",
    "how are you doing",
    "how are you",
    "thanks",
    "thank you",
    "bye",
    "good night",
    "okay"
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