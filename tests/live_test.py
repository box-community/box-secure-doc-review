"""Live end-to-end test against a real Box enterprise.

Runs the tutorial flow through the Flask routes: upload sample-tax-return.pdf,
fetch an expiring embed URL, then fetch a downscoped token and confirm it can
download that one file but cannot list a folder.

Works in a throwaway subfolder of LOAN_DOCS_FOLDER_ID and deletes it at the end.
Reads the same variables as .env.example, from the environment or a local .env.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from box_sdk_gen import (  # noqa: E402
    BoxAPIError,
    BoxClient,
    BoxDeveloperTokenAuth,
    CreateFolderParent,
)

from app import app  # noqa: E402
from box_client import get_box_client  # noqa: E402

REQUIRED_ENV = [
    "BOX_CLIENT_ID",
    "BOX_CLIENT_SECRET",
    "BOX_ENTERPRISE_ID",
    "LOAN_DOCS_FOLDER_ID",
]

# Box converts the file after upload; the embed link appears once it is ready.
EMBED_ATTEMPTS = 12
EMBED_RETRY_SECONDS = 5


def upload_sample(test_client) -> str:
    with open("sample-tax-return.pdf", "rb") as pdf:
        response = test_client.post(
            "/api/documents",
            data={"file": (pdf, "sample-tax-return.pdf")},
            content_type="multipart/form-data",
        )
    assert response.status_code == 201, f"upload returned {response.status_code}"
    return response.get_json()["file_id"]


def fetch_embed_url(test_client, file_id: str) -> str:
    for attempt in range(1, EMBED_ATTEMPTS + 1):
        response = test_client.get(f"/api/documents/{file_id}/embed")
        if response.status_code == 200:
            return response.get_json()["embed_url"]
        print(f"Embed link not ready (attempt {attempt}, status {response.status_code})")
        time.sleep(EMBED_RETRY_SECONDS)
    raise AssertionError("No embed link after waiting for conversion")


def check_downscoped_token(access_token: str, file_id: str, folder_id: str) -> None:
    scoped_client = BoxClient(auth=BoxDeveloperTokenAuth(token=access_token))

    content = scoped_client.downloads.download_file(file_id).read()
    assert content.startswith(b"%PDF"), "Downscoped token did not download the file"
    print("Downscoped token downloaded the file")

    try:
        scoped_client.folders.get_folder_items(folder_id)
    except BoxAPIError as error:
        print(f"Downscoped token was refused a folder listing ({error.response_info.status_code})")
        return
    raise AssertionError("Downscoped token could list a folder")


def main() -> None:
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    client = get_box_client()
    run_id = os.getenv("GITHUB_RUN_ID") or f"local-{int(time.time())}"
    folder = client.folders.create_folder(
        f"ci-run-{run_id}",
        CreateFolderParent(id=os.getenv("LOAN_DOCS_FOLDER_ID")),
    )
    # upload.py reads this at call time, so uploads land in the throwaway folder.
    os.environ["LOAN_DOCS_FOLDER_ID"] = folder.id

    try:
        test_client = app.test_client()

        file_id = upload_sample(test_client)
        print(f"Uploaded sample-tax-return.pdf as file {file_id}")

        box_name = client.files.get_file_by_id(file_id).name
        assert box_name == "sample-tax-return.pdf", f"File was named {box_name} in Box"

        embed_url = fetch_embed_url(test_client, file_id)
        assert embed_url.startswith("https://"), f"Unexpected embed URL: {embed_url}"
        print("Got an expiring embed URL")

        response = test_client.get(f"/api/documents/{file_id}/token")
        assert response.status_code == 200, f"token returned {response.status_code}"
        token = response.get_json()
        assert token.get("access_token"), "No access_token in response"
        assert token.get("expires_in", 0) > 0, "Token has no expiry"

        check_downscoped_token(token["access_token"], file_id, folder.id)

        print("Live test passed")
    finally:
        client.folders.delete_folder_by_id(folder.id, recursive=True)
        print(f"Deleted test folder {folder.id}")


if __name__ == "__main__":
    main()
