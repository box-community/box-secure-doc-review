# Box secure in-app document review

A minimal, runnable reference app that lets people read and annotate sensitive
documents **inside your own application** - no detour through the Box web app.

It implements the **upload → conversion → embed** flow with
[Box View](https://developer.box.com/guides/embed/box-view/): a backend uploads
a document to Box, Box converts it to a high-fidelity HTML5 rendering, and the
app requests a short-lived embed URL and drops it into an `<iframe>`. A second
page upgrades that bare iframe to
[Box Content Preview](https://developer.box.com/guides/embed/ui-elements/preview)
so reviewers can annotate in context.

This is the companion repository to the tutorial
**[Build secure in-app document review with Box View](https://developer.box.com/guides/tutorials/secure-in-app-document-review)**.

## What it does

| Capability | How |
| --- | --- |
| Upload a document to Box | `POST /2.0/files/content` (auto-triggers conversion) |
| Generate a short-lived preview URL | `GET /2.0/files/:id?fields=expiring_embed_link` |
| Mint a least-privilege browser token | `POST /oauth2/token` (token downscope) |
| Render in an iframe | `/review/<file_id>` |
| Annotate in context | `/annotate/<file_id>` (Box Content Preview) |

## Project layout

```
box-secure-doc-review/
├── app.py              # Flask backend (all routes)
├── box_client.py       # CCG Service Account auth
├── upload.py           # Upload a document, return its file ID
├── preview.py          # Expiring embed URL + downscoped token
├── review.html         # Iframe review page (Box View)
├── annotate.html       # Box Content Preview page with annotations
├── make_sample_pdf.py  # Generates sample-tax-return.pdf for testing
├── sample-tax-return.pdf
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- **Python 3.11+**
- A Box account with access to the [Developer Console](https://cloud.app.box.com/developers/console)
  and admin rights to authorize a Platform App. **A free
  [Box developer account](https://account.box.com/signup/developer) is enough for
  the core flow** (upload → embed → annotate); consumer/Individual accounts do
  not work. A paid Box Enterprise plan is only needed for the optional Box AI Q&A
  layer described in the tutorial.
- A **Client Credentials Grant (CCG)** Platform App with **Application Access**
  set to **App Access Only**, the scopes **Read all files and folders** and
  **Read and write all files and folders**, and the app **authorized** in the
  Admin Console.

See [Box View setup](https://developer.box.com/guides/embed/box-view/setup) for
the full app configuration walkthrough.

## Setup

1. **Clone and enter the project**

   ```bash
   git clone <your-fork-url> box-secure-doc-review
   cd box-secure-doc-review
   ```

2. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure credentials**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, and
   `BOX_ENTERPRISE_ID` from the Developer Console. Leave `LOAN_DOCS_FOLDER_ID=0`
   to upload to the Service Account's root folder, or set a folder ID.

   > **Never commit `.env`.** It is already in `.gitignore`.

4. **(For the annotate page) add your domain to the CORS allow-list** in the
   Developer Console. Box Content Preview calls the Box API from the browser, so
   the origin serving the page (e.g. `http://localhost:5000`) must be allow-listed.

## Run

```bash
python app.py
```

The server starts on `http://127.0.0.1:5000` (with auto-reload enabled).

> Flask loads routes at startup. If you add or change a route, restart the
> server (auto-reload handles edits after the first run). Do not use
> `debug=True` in production.

## Try it

1. **Upload the sample document** (or any PDF):

   ```bash
   curl -X POST http://127.0.0.1:5000/api/documents \
     -F "file=@sample-tax-return.pdf"
   # -> { "file_id": "1234567890" }
   ```

   Regenerate the sample any time with `python make_sample_pdf.py`.

2. **Review it in an iframe** - open in your browser (use the file ID from above):

   ```
   http://127.0.0.1:5000/review/1234567890
   ```

3. **Annotate it** with Box Content Preview:

   ```
   http://127.0.0.1:5000/annotate/1234567890
   ```

> Always open these pages **through the server** (`http://127.0.0.1:5000/...`),
> never by double-clicking the `.html` files. Opening over `file://` breaks the
> relative `fetch("/api/...")` calls, so the document never loads.

## How it works

The embed link is intentionally short-lived (about one minute) and is generated
**server-side, on demand** whenever a reviewer opens a document - it is never
stored or sent ahead of time. For the annotate page, the browser only ever
receives a **downscoped, file-scoped token** (see `PREVIEW_SCOPES` in
`preview.py`); the client secret and full access token stay on the server.

## Security notes

- Keep the client secret, enterprise ID, and full access token server-side.
- Keep **Application Access** at **App Access Only** unless you need more.
- Restrict the CORS allow-list to the exact origins running Content Preview.
- Downscope tokens before sending them to the browser (already done here).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `unauthorized_client` | Authorize the app in the Admin Console (Developer Console → Authorization → Review and Submit). |
| `invalid_client` | Check `BOX_CLIENT_ID` / `BOX_CLIENT_SECRET` / `BOX_ENTERPRISE_ID` in `.env`. |
| `404` on `/review/<id>` | Restart the server so the route registers. |
| Page shows only the header | You opened the HTML over `file://`. Use `http://127.0.0.1:5000/review/<id>`. |
| Annotate page CORS error | Add the serving origin to the app's CORS allow-list. |
| `No embed link returned` | Conversion may still be running, or the file type is unsupported. Wait and retry. |

## License

[MIT](./LICENSE)
