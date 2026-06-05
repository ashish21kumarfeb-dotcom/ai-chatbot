import json

from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


def classify_document(documents):

    sample_text = "\n".join(
        [doc.page_content for doc in documents[:3]]
    )

    prompt = f"""
Classify this document.

Possible types:

resume
handbook
policy
faq
contract
invoice
knowledge_base
other

Return JSON only.

Example:

{{
    "document_type": "resume"
}}

Document:

{sample_text}
"""

    response = llm.invoke(prompt)

    try:

        return json.loads(
            response.content
        )

    except:

        return {
            "document_type": "other"
        }