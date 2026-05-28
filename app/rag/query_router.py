import re


def detect_query_type(question: str):

    q = question.lower().strip()

    # remove punctuation
    q = re.sub(r"[^\w\s]", "", q)

    # =========================
    # FILE COUNT QUERIES
    # =========================
    count_keywords = [
        "how many",
        "count",
        "total files",
        "number of files"
    ]

    # =========================
    # FILE LISTING QUERIES
    # =========================
    listing_keywords = [
        "which files",
        "list files",
        "show files",
        "what files",
        "uploaded files"
    ]

    # =========================
    # FILE EXISTENCE QUERIES
    # =========================
    existence_keywords = [
        "is there any document",
        "is there any file",
        "are there documents",
        "are there files",
        "uploaded"
    ]

    # =========================
    # FILE TYPE QUERIES
    # =========================
    extension_keywords = [
        "pdf",
        "txt",
        "csv",
        "xlsx",
        "xls",
        "ppt",
        "pptx",
        "doc",
        "docx",
        "json",
        "html",
        "md",
        "markdown"
    ]

    # =========================
    # METADATA QUERIES
    # =========================
    metadata_keywords = [
        "filename",
        "file name",
        "extensions",
        "types of files"
    ]

    # -------------------------
    # COUNT
    # -------------------------
    for keyword in count_keywords:

        if keyword in q:

            return {
                "query_type": "metadata",
                "sub_type": "count"
            }

    # -------------------------
    # LIST FILES
    # -------------------------
    for keyword in listing_keywords:

        if keyword in q:

            return {
                "query_type": "metadata",
                "sub_type": "list"
            }

    # -------------------------
    # EXISTENCE
    # -------------------------
    for keyword in existence_keywords:

        if keyword in q:

            return {
                "query_type": "metadata",
                "sub_type": "existence"
            }

    # -------------------------
    # FILE TYPES
    # -------------------------
    for keyword in extension_keywords:

        if keyword in q:

            return {
                "query_type": "metadata",
                "sub_type": "file_type",
                "extension": keyword
            }

    # -------------------------
    # GENERAL METADATA
    # -------------------------
    for keyword in metadata_keywords:

        if keyword in q:

            return {
                "query_type": "metadata",
                "sub_type": "general_metadata"
            }

    # =========================
    # DEFAULT = SEMANTIC RAG
    # =========================
    return {
        "query_type": "semantic",
        "sub_type": "semantic_search"
    }