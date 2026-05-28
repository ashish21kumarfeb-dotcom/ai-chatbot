import os

UPLOAD_DIR = "app/uploads"

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".csv",
    ".xlsx",
    ".pptx",
    ".json",
    ".html",
    ".md"
}


def get_uploaded_files():

    if not os.path.exists(UPLOAD_DIR):
        return []

    return [
        f for f in os.listdir(UPLOAD_DIR)
        if os.path.isfile(
            os.path.join(UPLOAD_DIR, f)
        )
    ]


def get_files_by_extension(extension: str):

    files = get_uploaded_files()

    return [
        f for f in files
        if f.lower().endswith(extension)
    ]


def file_exists(filename: str):

    return os.path.exists(
        os.path.join(UPLOAD_DIR, filename)
    )


def is_duplicate(filename: str):

    return file_exists(filename)