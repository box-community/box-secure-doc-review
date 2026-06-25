import os
import tempfile

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file

from box_client import get_box_client
from upload import upload_document
from preview import get_embed_url, get_downscoped_token

load_dotenv()
app = Flask(__name__)


@app.route("/")
def index():
    """Friendly landing page with usage hints."""
    return jsonify(
        {
            "service": "Box secure in-app document review",
            "endpoints": {
                "POST /api/documents": "Upload a document (multipart 'file'), returns its file ID",
                "GET /api/documents/<file_id>/embed": "Get a fresh expiring embed URL",
                "GET /api/documents/<file_id>/token": "Get a downscoped, file-scoped token",
                "GET /review/<file_id>": "Iframe review page (Box View)",
                "GET /annotate/<file_id>": "Box Content Preview page with annotations",
                "GET /health": "Liveness check",
            },
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/documents", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "no file provided"}), 400

    incoming = request.files["file"]
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=f"_{incoming.filename}"
    ) as tmp:
        incoming.save(tmp.name)
        temp_path = tmp.name

    try:
        client = get_box_client()
        file_id = upload_document(client, temp_path)
    finally:
        os.remove(temp_path)

    return jsonify({"file_id": file_id}), 201


@app.route("/api/documents/<file_id>/embed", methods=["GET"])
def embed(file_id):
    client = get_box_client()
    embed_url = get_embed_url(client, file_id)
    return jsonify({"embed_url": embed_url}), 200


@app.route("/api/documents/<file_id>/token", methods=["GET"])
def token(file_id):
    client = get_box_client()
    return jsonify(get_downscoped_token(client, file_id)), 200


@app.route("/review/<file_id>")
def review_page(file_id):
    return send_file("review.html")


@app.route("/annotate/<file_id>")
def annotate_page(file_id):
    return send_file("annotate.html")


if __name__ == "__main__":
    app.run(port=5000, debug=True)
