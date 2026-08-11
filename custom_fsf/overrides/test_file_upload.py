from unittest import TestCase

import frappe
from frappe.core.doctype.file.exceptions import FileTypeNotAllowed

from custom_fsf.overrides.file_upload import check_upload_extension, extension_of


def setUpModule():
    # Bind a minimal Frappe context so frappe.throw()/_() work; no DB needed.
    if not getattr(frappe.local, "site", None):
        frappe.init(site="new_fsf")


class TestUploadExtensionCheck(TestCase):
    def _rejected(self, fname, allowlist=None):
        try:
            check_upload_extension(fname, allowlist)
            return False
        except FileTypeNotAllowed:
            return True

    def test_dangerous_extensions_blocked_without_allowlist(self):
        # No allowlist configured -> hard blocklist still applies.
        for fname in [
            "blan.php", "x.phtml", "a.phar", "b.pht", "page.html", "p.htm",
            "logo.svg", "d.xml", "s.js", "app.exe", "run.sh", "x.jsp", "m.bat",
        ]:
            self.assertTrue(self._rejected(fname, None), f"{fname} should be blocked")

    def test_extension_check_is_case_insensitive(self):
        for fname in ["shell.PHP", "evil.pHp", "X.PhTmL", "P.HtMl"]:
            self.assertTrue(self._rejected(fname, None), f"{fname} should be blocked")

    def test_double_extension_blocked_in_any_position(self):
        # Both orderings are rejected: a dangerous segment anywhere is enough,
        # because Apache mod_mime resolves the type right-to-left and would
        # still execute "archive.php.pdf" as PHP.
        self.assertTrue(self._rejected("invoice.pdf.php", None))
        self.assertTrue(self._rejected("archive.php.pdf", None))

    def test_safe_extensions_allowed_without_allowlist(self):
        for fname in ["doc.pdf", "pic.png", "photo.JPG", "sheet.xlsx", "data.csv", "clip.mov"]:
            self.assertFalse(self._rejected(fname, None), f"{fname} should be allowed")

    def test_allowlist_enforced_by_filename(self):
        allow = "PDF\nCSV\nPNG\nJPG"
        # dangerous stays blocked
        self.assertTrue(self._rejected("blan.php", allow))
        # not-on-allowlist named extension is blocked (this is the .php bypass fix)
        self.assertTrue(self._rejected("data.txt", allow))
        self.assertTrue(self._rejected("archive.zip", allow))
        # allowlisted extensions pass
        self.assertFalse(self._rejected("doc.pdf", allow))
        self.assertFalse(self._rejected("pic.png", allow))

    def test_extensionless_files_not_blocked(self):
        self.assertFalse(self._rejected("README", None))
        self.assertFalse(self._rejected("README", "PDF\nPNG"))

    def test_trailing_dot_and_space_do_not_bypass(self):
        # "shell.php." / "shell.php " land on disk as shell.php once the server
        # trims the padding, so they must be rejected as PHP.
        for fname in ["shell.php.", "shell.php ", "shell.php..", "shell.PHP . "]:
            self.assertTrue(self._rejected(fname, None), f"{fname} should be blocked")

    def test_nul_truncation_does_not_bypass(self):
        self.assertTrue(self._rejected("shell.php\x00.pdf", None))

    def test_inner_extension_does_not_bypass(self):
        # Apache mod_mime still executes shell.php.jpg as PHP.
        self.assertTrue(self._rejected("shell.php.jpg", None))
        self.assertTrue(self._rejected("x.phtml.png", "PNG\nJPG"))

    def test_dangerous_config_filenames_blocked(self):
        for fname in [".htaccess", ".HTACCESS", "web.config", ".user.ini", ".htpasswd"]:
            self.assertTrue(self._rejected(fname, None), f"{fname} should be blocked")

    def test_normal_business_files_still_upload(self):
        # Guard against over-blocking: these must keep working with a typical
        # business allowlist, otherwise the app looks crippled.
        allow = "PDF\nPNG\nJPG\nJPEG\nDOCX\nXLSX\nPPTX\nCSV\nTXT\nZIP"
        for fname in [
            "Chill (1).pdf", "report.v2.final.pdf", "photo.JPEG",
            "sheet.xlsx", "deck.pptx", "notes.txt", "bundle.zip",
        ]:
            self.assertFalse(self._rejected(fname, allow), f"{fname} should be allowed")

    def test_extension_of_helper(self):
        self.assertEqual(extension_of("a.b.PHP"), "PHP")
        self.assertEqual(extension_of("noext"), "")
        self.assertEqual(extension_of(""), "")
        self.assertEqual(extension_of(None), "")
