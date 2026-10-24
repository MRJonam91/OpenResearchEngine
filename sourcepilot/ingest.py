"""Convert imported bytes into passages with source locators."""

from __future__ import annotations

from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
import re
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from .network import fetch_public

MAX_IMPORT_BYTES = 20 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".html", ".htm", ".pdf", ".docx"}
MAX_DOCUMENT_EXPANDED_BYTES = 80 * 1024 * 1024


def fetch_url(url: str) -> tuple[str, bytes, str]:
    data, media_type, final_url = fetch_public(url, MAX_IMPORT_BYTES)
    suffix = {"text/html": ".html", "application/xhtml+xml": ".html", "text/plain": ".txt", "application/pdf": ".pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx"}.get(media_type)
    if suffix is None:
        raise ValueError(f"Unsupported URL content type: {media_type}")
    host = urlsplit(final_url).hostname or "webpage"
    title = Path(urlsplit(final_url).path).name or host
    name = f"{title}{suffix}" if not title.lower().endswith(suffix) else title
    return name, data, final_url


def _docx(data: bytes) -> list[tuple[str, str]]:
    try:
        with ZipFile(BytesIO(data)) as archive:
            if len(archive.infolist()) > 10000 or sum(info.file_size for info in archive.infolist()) > MAX_DOCUMENT_EXPANDED_BYTES:
                raise ValueError("DOCX expanded content exceeds the limit")
            xml = archive.read("word/document.xml").decode("utf-8-sig")
        if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
            raise ValueError("DOCX DTD/entity declarations are not supported")
        root = ElementTree.fromstring(xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        body = root.find(f"{ns}body")
        if body is None:
            raise ValueError("DOCX has no document body")
        text = lambda node: "".join(part.text or "" for part in node.iter(f"{ns}t")).strip()
        result = []
        paragraph = table = 0
        for node in body:
            if node.tag == f"{ns}p":
                paragraph += 1
                if text(node):
                    result.append((f"paragraph {paragraph}", text(node)))
            elif node.tag == f"{ns}tbl":
                table += 1
                for row_number, row in enumerate(node.findall(f"{ns}tr"), 1):
                    value = " | ".join(text(cell) for cell in row.findall(f"{ns}tc"))
                    if value.strip(" |"):
                        result.append((f"table {table}, row {row_number}", value))
        if not result:
            raise ValueError("DOCX has no extractable text")
        return result
    except (BadZipFile, KeyError, ElementTree.ParseError, RuntimeError, UnicodeError) as exc:
        raise ValueError("Could not read DOCX document") from exc


def _paragraphs(text: str, prefix: str = "lines") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    current: list[str] = []
    start = 1

    def flush(end: int) -> None:
        nonlocal current
        value = " ".join(line.strip() for line in current).strip()
        if value:
            result.append((f"{prefix} {start}-{end}", value))
        current = []

    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            if current:
                flush(number - 1)
        else:
            if prefix == "lines" and current and re.match(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)", line):
                flush(number - 1)
            if not current:
                start = number
            current.append(line)
    if current:
        flush(len(lines))
    return result


class _VisibleHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value and not self.skip_depth:
            self.parts.append((f"line {self.getpos()[0]}", value))


def extract_passages(name: str, data: bytes) -> list[tuple[str, str]]:
    extension = Path(name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or 'none'}")
    if not data:
        raise ValueError("Cannot import an empty file")
    if len(data) > MAX_IMPORT_BYTES:
        raise ValueError("File exceeds the 20 MB limit")
    if extension == ".docx":
        return _docx(data)
    if extension == ".pdf":
        from pypdf import PdfReader

        try:
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise ValueError("Encrypted PDF is not supported")
            passages: list[tuple[str, str]] = []
            for page_number, page in enumerate(reader.pages, 1):
                for paragraph_number, (_, value) in enumerate(_paragraphs(page.extract_text() or ""), 1):
                    passages.append((f"page {page_number}, paragraph {paragraph_number}", value))
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}") from exc
        if not passages:
            raise ValueError("PDF has no extractable text; OCR is not available")
        return passages
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Text file must be UTF-8") from exc
    if extension in {".html", ".htm"}:
        parser = _VisibleHTML()
        parser.feed(text)
        passages = parser.parts
    else:
        passages = _paragraphs(text)
    if not passages:
        raise ValueError("File has no extractable text")
    return passages
