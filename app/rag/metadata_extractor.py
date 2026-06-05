import json

from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


def extract_metadata(
    documents,
    classification
):

    document_type = classification.get(
        "document_type",
        "other"
    )

    sample_text = "\n".join(
        [doc.page_content for doc in documents[:3]]
    )

    if document_type == "resume":

        prompt = f"""
Extract person name.

Return JSON only.

Example:

{{
    "person_name":
    "Nitish Kumar Gupta"
}}

Document:

{sample_text}
"""

    elif document_type in [
        "handbook",
        "policy",
        "faq",
        "knowledge_base"
    ]:

        prompt = f"""
Extract company name.

Return JSON only.

Example:

{{
    "company_name":
    "Acme Corp"
}}

Document:

{sample_text}
"""

    else:

        return {}

    response = llm.invoke(prompt)

    try:

        return json.loads(
            response.content
        )

    except:

        return {}