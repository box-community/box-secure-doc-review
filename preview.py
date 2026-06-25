from box_sdk_gen import BoxClient

# Least-privilege scopes for client-side Box Content Preview + annotations.
PREVIEW_SCOPES = [
    "base_preview",
    "item_preview",
    "annotation_edit",
    "annotation_view_all",
    "item_download",
]


def get_embed_url(client: BoxClient, file_id: str) -> str:
    """Return a short-lived expiring embed URL for the file.

    The link expires about a minute after it is generated, so it is created
    fresh on every request and dropped straight into an <iframe>.
    """
    file = client.files.get_file_by_id(
        file_id,
        fields=["expiring_embed_link"],
    )

    if not file.expiring_embed_link:
        raise RuntimeError(
            "No embed link returned. The file may still be converting, "
            "or preview is not available for this file type."
        )

    return file.expiring_embed_link.url


def get_downscoped_token(client: BoxClient, file_id: str) -> dict:
    """Exchange the Service Account token for a downscoped, file-scoped token.

    Safe to send to the browser: it is limited to PREVIEW_SCOPES on a single
    file and is short-lived.
    """
    token = client.auth.downscope_token(
        PREVIEW_SCOPES,
        resource=f"https://api.box.com/2.0/files/{file_id}",
    )
    return {
        "access_token": token.access_token,
        "expires_in": token.expires_in,
    }
