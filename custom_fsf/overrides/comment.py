from urllib.parse import urlsplit

import bleach
from bs4 import BeautifulSoup


# Keep this list aligned with the formats exposed by Frappe's Comment editor.
# A positive allowlist prevents new HTML elements from becoming implicitly
# trusted when Frappe's broader, general-purpose sanitizer changes.
SAFE_COMMENT_TAGS = frozenset(
    {
        "a",
        "b",
        "blockquote",
        "br",
        "code",
        "div",
        "em",
        "i",
        "img",
        "li",
        "ol",
        "p",
        "pre",
        "s",
        "span",
        "strike",
        "strong",
        "u",
        "ul",
    }
)

# These elements must not leave their contents behind when their tags are
# removed. In particular, CSS from a stripped <style> tag should not appear as
# text in the saved comment.
DROP_WITH_CONTENT_TAGS = frozenset(
    {"embed", "form", "iframe", "noscript", "object", "script", "style", "template"}
)

SAFE_URL_PROTOCOLS = frozenset({"http", "https", "mailto"})

_FORMATTING_CLASSES = frozenset(
    {
        "ql-align-center",
        "ql-align-justify",
        "ql-align-right",
        "ql-direction-rtl",
        *(f"ql-indent-{level}" for level in range(1, 9)),
    }
)

_SAFE_CLASSES_BY_TAG = {
    "blockquote": _FORMATTING_CLASSES,
    "div": _FORMATTING_CLASSES | {"ql-editor", "read-mode"},
    "li": _FORMATTING_CLASSES,
    "p": _FORMATTING_CLASSES,
    "pre": _FORMATTING_CLASSES | {"ql-syntax"},
    "span": {"mention", "ql-mention-denotation-char", "ql-ui"},
}

_MENTION_ATTRIBUTES = frozenset(
    {"data-denotation-char", "data-id", "data-is-group", "data-value"}
)


def _is_safe_url(value):
    value = value.strip()
    if not value:
        return False

    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return not parsed.scheme or parsed.scheme.lower() in SAFE_URL_PROTOCOLS


def _is_local_image(value):
    value = value.strip()
    return value == "#broken-image" or value.startswith(("/files/", "/private/files/"))


def _allow_comment_attribute(tag, name, value):
    """Allow only attributes required by the Frappe Comment editor."""
    if name == "class":
        classes = frozenset(value.split())
        return bool(classes) and classes <= _SAFE_CLASSES_BY_TAG.get(tag, frozenset())

    if name == "dir":
        return tag in {"blockquote", "div", "li", "p", "pre"} and value.lower() in {
            "auto",
            "ltr",
            "rtl",
        }

    if tag == "a":
        return name == "title" or (name == "href" and _is_safe_url(value))

    if tag == "img":
        if name in {"alt", "title"}:
            return True
        return name == "src" and _is_local_image(value)

    if tag == "li" and name == "data-list":
        return value in {"bullet", "checked", "ordered", "unchecked"}

    if tag == "span" and name in _MENTION_ATTRIBUTES:
        if name == "data-denotation-char":
            return value == "@"
        if name == "data-is-group":
            return value in {"false", "true"}
        return True

    return False


def sanitize_comment_content(content):
    """Return comment HTML restricted to the Comment editor's safe subset."""
    if not isinstance(content, str) or "<" not in content:
        return content

    # This pre-pass improves the saved output; Bleach below remains the security
    # boundary and handles malformed HTML using its HTML5 parser.
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup.find_all(DROP_WITH_CONTENT_TAGS):
        tag.decompose()

    return bleach.clean(
        str(soup),
        tags=SAFE_COMMENT_TAGS,
        attributes=_allow_comment_attribute,
        protocols=SAFE_URL_PROTOCOLS,
        strip=True,
        strip_comments=True,
    )


def sanitize_comment_html(doc, method=None):
    """Restrict user-authored Comment content before every insert or update."""
    if getattr(doc, "comment_type", None) != "Comment":
        return

    doc.content = sanitize_comment_content(doc.content)
