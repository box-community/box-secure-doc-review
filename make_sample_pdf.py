"""Generate a small, valid sample PDF for testing the upload + preview flow.

Pure standard library - no dependencies. Run:

    python make_sample_pdf.py

This writes sample-tax-return.pdf in the current directory.
"""

OUTPUT = "sample-tax-return.pdf"

LINES = [
    "Sample Tax Return - Form 1040",
    "",
    "Taxpayer: Jane Q. Borrower",
    "Tax year: 2025",
    "Adjusted gross income: $128,400",
    "Total tax: $21,360",
    "",
    "This is a sample document for the Box secure in-app",
    "document review tutorial. It is not a real tax return.",
]


def _content_stream() -> bytes:
    parts = ["BT", "/F1 18 Tf", "72 720 Td", "20 TL"]
    for line in LINES:
        # Escape PDF string special characters.
        safe = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        parts.append(f"({safe}) Tj")
        parts.append("T*")
    parts.append("ET")
    return ("\n".join(parts)).encode("latin-1")


def build_pdf() -> bytes:
    content = _content_stream()

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
        + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(pdf)
    count = len(objects) + 1
    pdf += f"xref\n0 {count}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()

    pdf += (
        b"trailer\n<< /Size " + str(count).encode() + b" /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF\n"
    )
    return bytes(pdf)


if __name__ == "__main__":
    with open(OUTPUT, "wb") as f:
        f.write(build_pdf())
    print(f"Wrote {OUTPUT}")
