import os


def extract_text_from_upload(filename: str, content: bytes) -> dict:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        parts = []
        for i in range(doc.page_count):
            page = doc.load_page(i)
            parts.append(page.get_text("text") or "")
        text = "\n".join(parts).strip()
        return {
            "text": text,
            "meta": {"type": "pdf", "pages": doc.page_count}
        }

    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1"):
        try:
            text = content.decode(enc).strip()
            return {
                "text": text,
                "meta": {"type": "text", "encoding": enc, "ext": ext or ""}
            }
        except Exception:
            continue

    return {"text": "", "meta": {"type": "unknown", "ext": ext or ""}}
