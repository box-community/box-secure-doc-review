import os

from box_sdk_gen import (
    BoxClient,
    UploadFileAttributes,
    UploadFileAttributesParentField,
)


def upload_document(
    client: BoxClient, file_path: str, file_name: str | None = None
) -> str:
    """Upload a document to the loan documents folder and return its file ID.

    Pass file_name to name the file in Box differently from file_path, for
    example the original name of a browser upload saved to a temporary file.

    Uploading triggers Box conversion automatically, so the file is ready
    to preview moments later.
    """
    folder_id = os.getenv("LOAN_DOCS_FOLDER_ID", "0")
    file_name = os.path.basename(file_name or file_path)

    with open(file_path, "rb") as file_stream:
        uploaded = client.uploads.upload_file(
            UploadFileAttributes(
                name=file_name,
                parent=UploadFileAttributesParentField(id=folder_id),
            ),
            file_stream,
        )

    file_id = uploaded.entries[0].id
    print(f"Uploaded {file_name} -> file ID {file_id}")
    return file_id
