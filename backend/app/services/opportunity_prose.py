from __future__ import annotations

import html
import re
from html.parser import HTMLParser

MAX_PROSE_CHARS = 20000
HTML_TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")
SKIP_TAGS = {"script", "style", "iframe", "noscript", "svg", "head", "object", "embed"}
HEADING_PREFIX = {
    "h1": "## ",
    "h2": "## ",
    "h3": "### ",
    "h4": "### ",
    "h5": "#### ",
    "h6": "#### ",
}
HEADING_LINE_RE = re.compile(
    r"^(about(?:\s+the)?\s+(?:role|company|us|opportunity|team)|"
    r"what you(?:'ll| will) do|"
    r"what we(?:'re| are) looking for|"
    r"responsibilities|requirements|qualifications|"
    r"nice(?:\s+|-)?to(?:\s+|-)?have|benefits|compensation|"
    r"who you are|who we are|the role|about this role)\s*:?\s*$",
    re.IGNORECASE,
)
HEADING_SPLIT_RE = re.compile(
    r"(?<!\S)(About(?:\s+the)?\s+(?:role|company|us|opportunity|team)|"
    r"What you(?:'ll| will) do|"
    r"What we(?:'re| are) looking for|"
    r"Responsibilities|Requirements|Qualifications|"
    r"Nice(?:\s+|-)?to(?:\s+|-)?have|Benefits|Compensation|"
    r"Who you are|Who we are|The role|About this role)\s*:?"
    r"(?=\s+(?-i:[A-Z0-9•\-]))",
    re.IGNORECASE,
)
LIST_LINE_RE = re.compile(r"^\s*(?:[-*•–]|\d+[.)])\s+")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,4}\s+\S")
BOLD_MARKDOWN_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_MARKDOWN_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
FANCY_DASH_RE = re.compile(r"\s*[\u2014\u2013]\s*")


def looks_like_html(value: str) -> bool:
    return bool(HTML_TAG_RE.search(value or ""))


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    text = normalize_description(value)
    return text or None


def normalize_description(value: str | None) -> str:
    text = (value or "").replace("\xa0", " ").strip()
    if not text:
        return ""
    if looks_like_html(text) or "&lt;" in text[:400]:
        text = html_to_markdown(text)
    return normalize_plain_text(text)[:MAX_PROSE_CHARS]


def html_to_markdown(value: str) -> str:
    raw = html.unescape((value or "").strip())
    if looks_like_html(raw):
        parser = _HtmlMarkdownParser()
        try:
            parser.feed(raw)
            parser.close()
        except Exception:
            return normalize_plain_text(re.sub(r"<[^>]+>", "\n", raw))
        return _cleanup_markdown(parser.text())
    return raw


def normalize_plain_text(value: str) -> str:
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return ""
    if "\n" not in text:
        text = _split_collapsed_headings(text)
    lines = [_clean_line(line) for line in text.split("\n")]
    out: list[str] = []
    for line in lines:
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        heading = _heading_markdown(line)
        if heading:
            if out and out[-1] != "":
                out.append("")
            out.append(heading)
            out.append("")
            continue
        bullet = _as_list_item(line)
        if bullet:
            out.append(bullet)
            continue
        out.append(line)
    return _cleanup_markdown("\n".join(out))


def _split_collapsed_headings(text: str) -> str:
    if MARKDOWN_HEADING_RE.match(text) or LIST_LINE_RE.match(text):
        return text
    parts = HEADING_SPLIT_RE.split(text)
    if len(parts) < 3:
        return text
    chunks: list[str] = []
    index = 0
    while index < len(parts):
        piece = parts[index].strip()
        if not piece:
            index += 1
            continue
        if HEADING_LINE_RE.match(piece):
            chunks.append(f"### {piece.rstrip(':').strip()}")
            index += 1
            continue
        chunks.append(piece)
        index += 1
    return "\n\n".join(chunks)


def _heading_markdown(line: str) -> str | None:
    if MARKDOWN_HEADING_RE.match(line):
        return line
    match = HEADING_LINE_RE.match(line)
    if not match:
        return None
    return f"### {match.group(1).rstrip(':').strip()}"


def _as_list_item(line: str) -> str | None:
    if line.startswith(("- ", "* ", "• ")) or re.match(r"^\d+[.)]\s+", line):
        numbered = re.match(r"^(\d+)[.)]\s+(.*)$", line)
        if numbered:
            return f"{numbered.group(1)}. {numbered.group(2).strip()}"
        return f"- {re.sub(r'^[-*•–]\s+', '', line).strip()}"
    return None


def _strip_emphasis_markers(line: str) -> str:
    """Drop markdown bold/italic markers so listings don't show raw ** or *."""
    text = BOLD_MARKDOWN_RE.sub(r"\1", line)
    text = ITALIC_MARKDOWN_RE.sub(r"\1", text)
    return text.replace("**", "").replace("__", "")


def _normalize_dashes(line: str) -> str:
    """Replace em/en dashes with a plain hyphen (avoids AI-slop punctuation)."""
    return FANCY_DASH_RE.sub(" - ", line)


def _clean_line(line: str) -> str:
    text = re.sub(r"[ \t]+", " ", line).strip()
    text = _strip_emphasis_markers(text)
    text = _normalize_dashes(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _cleanup_markdown(text: str) -> str:
    lines = [_clean_line(line) for line in text.replace("\r\n", "\n").split("\n")]
    out: list[str] = []
    blank = False
    for line in lines:
        if not line:
            if out and not blank:
                out.append("")
            blank = True
            continue
        blank = False
        out.append(line)
    return "\n".join(out).strip()


class _HtmlMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip = 0
        self._lists: list[str] = []
        self._indexes: list[int] = []
        self._li = 0

    def text(self) -> str:
        return "".join(self._chunks)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip += 1
            return
        if self._skip:
            return
        if tag in HEADING_PREFIX:
            self._break()
            self._chunks.append(HEADING_PREFIX[tag])
        elif tag == "br":
            self._chunks.append("\n")
        elif tag in {"p", "div", "section", "article", "blockquote", "tr"}:
            if self._li == 0:
                self._break()
        elif tag in {"ul", "ol"}:
            self._break()
            self._lists.append(tag)
            self._indexes.append(0)
        elif tag == "li":
            self._break()
            self._li += 1
            if self._lists and self._lists[-1] == "ol":
                self._indexes[-1] += 1
                self._chunks.append(f"{self._indexes[-1]}. ")
            else:
                self._chunks.append("- ")
        # strong/em: keep plain text only — no ** / * markers in stored prose

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self._skip:
            self._skip -= 1
            return
        if self._skip:
            return
        if tag in HEADING_PREFIX or tag in {"p", "div", "section", "article", "blockquote"}:
            if self._li == 0:
                self._break()
        elif tag in {"ul", "ol"}:
            if self._lists:
                self._lists.pop()
                self._indexes.pop()
            self._break()
        elif tag == "li":
            if self._li:
                self._li -= 1
            self._break()

    def handle_data(self, data: str) -> None:
        if self._skip or not data:
            return
        self._chunks.append(re.sub(r"[ \t\r\f\v]+", " ", data))

    def _break(self) -> None:
        if self._chunks and not self._chunks[-1].endswith("\n"):
            self._chunks.append("\n")
