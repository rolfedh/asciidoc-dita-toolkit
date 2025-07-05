"""
Test suite for the CLI interface of the AsciiDoc DITA toolkit.
"""

import os
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from asciidoc_dita_toolkit.asciidoc_dita import toolkit


class TestCLI(unittest.TestCase):
    """Test cases for the CLI interface."""

    def test_discover_plugins(self):
        """Test that plugin discovery works correctly."""
        plugins = toolkit.discover_plugins()
        self.assertIsInstance(plugins, list)
        self.assertIn("EntityReference", plugins)
        self.assertIn("ContentType", plugins)  # ContentType file exists, but may not be registered

    @patch("sys.stdout", new_callable=StringIO)
    def test_list_plugins(self, mock_stdout):
        """Test the --list-plugins functionality."""
        toolkit.print_plugin_list()
        output = mock_stdout.getvalue()
        self.assertIn("Available plugins:", output)
        self.assertIn("EntityReference", output)
        # ContentType may or may not be listed depending on ADT_ENABLE_CONTENT_TYPE

    @patch("sys.argv", ["toolkit", "--list-plugins"])
    @patch("sys.exit")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_list_plugins(self, mock_stdout, mock_exit):
        """Test main function with --list-plugins argument."""
        toolkit.main()
        mock_exit.assert_called_once_with(0)
        output = mock_stdout.getvalue()
        self.assertIn("Available plugins:", output)

    @patch("sys.argv", ["toolkit"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_no_args(self, mock_stdout):
        """Test main function with no arguments shows help."""
        toolkit.main()
        output = mock_stdout.getvalue()
        self.assertIn("usage:", output)

    def test_plugin_loading_with_missing_function(self):
        """Test handling of plugins missing register_subcommand function."""
        with patch("sys.argv", ["toolkit"]), patch(
            "sys.stderr", new_callable=StringIO
        ) as mock_stderr, patch("sys.stdout", new_callable=StringIO) as mock_stdout, patch(
            "asciidoc_dita_toolkit.asciidoc_dita.toolkit.discover_plugins"
        ) as mock_discover, patch(
            "importlib.import_module"
        ) as mock_import:

            mock_discover.return_value = ["test_plugin"]
            mock_module = MagicMock()
            del mock_module.register_subcommand  # Remove the function
            mock_import.return_value = mock_module

            toolkit.main()
            error_output = mock_stderr.getvalue()
            self.assertIn("missing register_subcommand function", error_output)

    def test_plugin_loading_with_import_error(self):
        """Test handling of plugin import errors."""
        with patch("sys.argv", ["toolkit"]), patch(
            "sys.stderr", new_callable=StringIO
        ) as mock_stderr, patch("sys.stdout", new_callable=StringIO) as mock_stdout, patch(
            "asciidoc_dita_toolkit.asciidoc_dita.toolkit.discover_plugins"
        ) as mock_discover, patch(
            "importlib.import_module", side_effect=ImportError("Test import error")
        ):

            mock_discover.return_value = ["broken_plugin"]

            toolkit.main()
            error_output = mock_stderr.getvalue()
            self.assertIn("Error loading plugin", error_output)

    @patch("sys.argv", ["toolkit", "EntityReference", "--help"])
    def test_plugin_help(self):
        """Test that plugin help works correctly."""

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                toolkit.main()
        # argparse exits with code 0 for --help
        self.assertEqual(cm.exception.code, 0)

    @patch.dict(os.environ, {}, clear=True)
    @patch("sys.argv", ["toolkit", "--help"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_content_type_disabled_by_default(self, mock_stdout):
        """Test that ContentType plugin is disabled by default."""
        try:
            toolkit.main()
        except SystemExit:
            pass  # argparse calls sys.exit after showing help

        output = mock_stdout.getvalue()
        # ContentType should not appear in subcommands when disabled
        self.assertNotIn("ContentType", output)

    @patch.dict(os.environ, {"ADT_ENABLE_CONTENT_TYPE": "true"})
    @patch("sys.argv", ["toolkit", "--help"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_content_type_enabled_via_env(self, mock_stdout):
        """Test that ContentType plugin can be enabled via environment variable."""
        try:
            toolkit.main()
        except SystemExit:
            pass  # argparse calls sys.exit after showing help

        output = mock_stdout.getvalue()
        # ContentType should appear in subcommands when enabled
        self.assertIn("ContentType", output)

    @patch.dict(os.environ, {"ADT_ENABLE_CONTENT_TYPE": "false"})
    @patch("sys.argv", ["toolkit", "--help"])
    @patch("sys.stdout", new_callable=StringIO)
    def test_content_type_explicitly_disabled(self, mock_stdout):
        """Test that ContentType plugin can be explicitly disabled."""
        try:
            toolkit.main()
        except SystemExit:
            pass  # argparse calls sys.exit after showing help

        output = mock_stdout.getvalue()
        # ContentType should not appear when explicitly disabled
        self.assertNotIn("ContentType", output)


class TestEntityReferencePlugin(unittest.TestCase):
    """Test cases for the EntityReference plugin."""

    def setUp(self):
        """Set up test fixtures."""
        from asciidoc_dita_toolkit.asciidoc_dita.plugins import EntityReference

        self.plugin = EntityReference

    def test_replace_entities_supported(self):
        """Test that supported entities are not replaced."""
        input_line = "This &amp; that &lt; other"
        result = self.plugin.replace_entities(input_line)
        self.assertEqual(result, input_line)

    def test_replace_entities_unsupported(self):
        """Test that unsupported entities are replaced."""
        input_line = "Copyright &copy; 2024"
        result = self.plugin.replace_entities(input_line)
        self.assertEqual(result, "Copyright {copy} 2024")

    def test_replace_entities_unknown(self):
        """Test handling of unknown entities."""
        input_line = "Unknown &unknown; entity"
        with patch("builtins.print") as mock_print:
            result = self.plugin.replace_entities(input_line)
            mock_print.assert_called_with("Warning: No AsciiDoc attribute for &unknown;")
            self.assertEqual(result, input_line)


class TestContentTypePlugin(unittest.TestCase):
    """Test cases for the ContentType plugin."""

    def setUp(self):
        """Set up test fixtures."""
        from asciidoc_dita_toolkit.asciidoc_dita.plugins import ContentType

        self.plugin = ContentType

    def test_get_content_type_from_filename(self):
        """Test content type detection from filename."""
        test_cases = [
            ("assembly_test.adoc", "ASSEMBLY"),
            ("assembly-test.adoc", "ASSEMBLY"),
            ("con_test.adoc", "CONCEPT"),
            ("con-test.adoc", "CONCEPT"),
            ("proc_test.adoc", "PROCEDURE"),
            ("proc-test.adoc", "PROCEDURE"),
            ("ref_test.adoc", "REFERENCE"),
            ("ref-test.adoc", "REFERENCE"),
            ("snip_test.adoc", "SNIPPET"),
            ("snip-test.adoc", "SNIPPET"),
            ("other_test.adoc", None),
        ]

        for filename, expected in test_cases:
            with self.subTest(filename=filename):
                result = self.plugin.get_content_type_from_filename(filename)
                self.assertEqual(result, expected)

    def test_detect_existing_content_type(self):
        """Test detection of existing content type attributes."""
        test_cases = [
            ([("text", "\n"), (":_mod-docs-content-type: CONCEPT", "\n")], ("CONCEPT", 1, "current")),
            ([("text", "\n"), (":_content-type: PROCEDURE", "\n")], ("PROCEDURE", 1, "deprecated_content")),
            ([("text", "\n"), (":_module-type: REFERENCE", "\n")], ("REFERENCE", 1, "deprecated_module")),
            ([("text", "\n"), ("no content type", "\n")], (None, None, None)),
        ]
        
        for lines, expected in test_cases:
            with self.subTest(lines=lines):
                result = self.plugin.detect_existing_content_type(lines)
                self.assertEqual(result, expected)

    def test_analyze_title_style(self):
        """Test content type suggestions based on title analysis."""
        test_cases = [
            ("= Creating a new project", "PROCEDURE"),
            ("= Docker commands reference", "REFERENCE"),
            ("= Getting started guide", "ASSEMBLY"),
            ("= What is containerization", "CONCEPT"),
            (None, None),
        ]
        
        for title, expected in test_cases:
            with self.subTest(title=title):
                result = self.plugin.analyze_title_style(title)
                self.assertEqual(result, expected)

    def test_analyze_content_patterns(self):
        """Test content type suggestions based on content analysis."""
        test_cases = [
            ("This document includes:\ninclude::other.adoc[]", "ASSEMBLY"),
            ("1. First step\n2. Second step\n.Procedure", "PROCEDURE"),
            ("|====\n|Column 1|Column 2\n|Value 1|Value 2\n|====", "REFERENCE"),
            ("This is just regular content.", None),
        ]
        
        for content, expected in test_cases:
            with self.subTest(content=content):
                result = self.plugin.analyze_content_patterns(content)
                self.assertEqual(result, expected)

    def test_get_document_title(self):
        """Test extraction of document title from file lines."""
        test_cases = [
            ([("= Main Title", "\n"), ("content", "\n")], "Main Title"),
            ([("# Markdown Title", "\n"), ("content", "\n")], "Markdown Title"),
            ([("content", "\n"), ("= Title Later", "\n")], "Title Later"),
            ([("content", "\n"), ("no title", "\n")], None),
            ([], None),
        ]
        
        for lines, expected in test_cases:
            with self.subTest(lines=lines):
                result = self.plugin.get_document_title(lines)
                self.assertEqual(result, expected)

    def test_ensure_blank_line_below(self):
        """Test ensuring blank line after content type attribute."""
        # Test case: line at end of file
        lines = [("content", "\n"), (":_mod-docs-content-type: CONCEPT", "\n")]
        result = self.plugin.ensure_blank_line_below(lines, 1)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[2], ("", "\n"))
        
        # Test case: no blank line after attribute
        lines = [("content", "\n"), (":_mod-docs-content-type: CONCEPT", "\n"), ("more content", "\n")]
        result = self.plugin.ensure_blank_line_below(lines, 1)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[2], ("", "\n"))
        
        # Test case: blank line already exists
        lines = [("content", "\n"), (":_mod-docs-content-type: CONCEPT", "\n"), ("", "\n"), ("more content", "\n")]
        result = self.plugin.ensure_blank_line_below(lines, 1)
        self.assertEqual(len(result), 4)  # Should not add another blank line


if __name__ == "__main__":
    unittest.main()
