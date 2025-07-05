"""
Plugin for the AsciiDoc DITA toolkit: ContentType

This plugin adds a :_mod-docs-content-type: label in .adoc files where those are missing, based on filename.
"""

__description__ = "Add a :_mod-docs-content-type: label in .adoc files where those are missing, based on filename."

import os
import re
import sys

from ..file_utils import common_arg_parser, process_adoc_files, read_text_preserve_endings, write_text_preserve_endings, is_plugin_enabled


class Highlighter:
    """Simple text highlighter for console output."""

    def __init__(self, text):
        self.text = text

    def warn(self):
        return f"\033[0;31m{self.text}\033[0m"

    def bold(self):
        return f"\033[1m{self.text}\033[0m"

    def highlight(self):
        return f"\033[0;36m{self.text}\033[0m"

    def success(self):
        return f"\033[0;32m{self.text}\033[0m"


def get_content_type_from_filename(filename):
    """
    Determine content type based on filename prefix.

    Args:
        filename: Name of the file (without path)

    Returns:
        Content type string or None if no pattern matches
    """
    prefixes = {
        ("assembly_", "assembly-"): "ASSEMBLY",
        ("con_", "con-"): "CONCEPT",
        ("proc_", "proc-"): "PROCEDURE",
        ("ref_", "ref-"): "REFERENCE",
        ("snip_", "snip-"): "SNIPPET",
    }

    for prefix_group, content_type in prefixes.items():
        if any(filename.startswith(prefix) for prefix in prefix_group):
            return content_type
    return None


def detect_existing_content_type(lines):
    """
    Detect existing content type attributes in file.

    Args:
        lines: List of (text, ending) tuples from file

    Returns:
        tuple: (content_type, line_index, attribute_type) or (None, None, None)
        attribute_type: 'current', 'deprecated_content', 'deprecated_module'
    """
    for i, (text, _) in enumerate(lines):
        stripped = text.strip()
        
        # Current format
        if stripped.startswith(":_mod-docs-content-type:"):
            value = stripped.split(":", 2)[-1].strip()
            return (value, i, 'current')
        
        # Deprecated formats
        if stripped.startswith(":_content-type:"):
            value = stripped.split(":", 2)[-1].strip()
            return (value, i, 'deprecated_content')
            
        if stripped.startswith(":_module-type:"):
            value = stripped.split(":", 2)[-1].strip()
            return (value, i, 'deprecated_module')
    
    return (None, None, None)


def prompt_user_for_content_type(suggested_type=None):
    """
    Prompt user to select content type interactively with smart pre-selection.

    Args:
        suggested_type: Suggested content type based on analysis

    Returns:
        Selected content type string or None if skipped
    """
    options = [
        "ASSEMBLY",
        "CONCEPT", 
        "PROCEDURE",
        "REFERENCE",
        "SNIPPET",
        "TBD"
    ]
    
    # Find suggested option index
    suggested_index = None
    if suggested_type and suggested_type in options:
        suggested_index = options.index(suggested_type) + 1
    
    if suggested_type:
        print(f"\nContent type not specified. Based on analysis, this appears to be a {Highlighter(suggested_type).highlight()}.")
        print("\nSelect content type:")
    else:
        print("\nNo content type detected. Please select:")
    
    for i, option in enumerate(options, 1):
        if i == suggested_index:
            print(f"[{i}] ✓ {Highlighter(option).highlight()} (recommended)")
        elif option == "TBD" and not suggested_index:
            print(f"[{i}] ✓ {Highlighter(option).highlight()} (type not detected)")
        else:
            print(f"[{i}]   {option}")
    print("[7] Skip this file")
    print("[8] Quit")
    # Set default choice message
    default_choice = suggested_index if suggested_index else ""
    prompt_msg = f"Choice (1-8) [{suggested_index}]: " if suggested_index else "Choice (1-8): "
    while True:
        try:
            choice = input(prompt_msg).strip()
            # Use suggested default if user just presses Enter
            if choice == "" and suggested_index:
                choice = str(suggested_index)
            elif choice == "":
                # No suggestion, default to 6 (TBD)
                choice = "6"
            if choice == "7":
                return None
            if choice == "8":
                print("Exiting at user request.")
                sys.exit(0)
            choice_num = int(choice)
            if 1 <= choice_num <= 6:
                return options[choice_num - 1]
            else:
                print("Please enter a number between 1 and 8.")
        except (ValueError, KeyboardInterrupt, EOFError):
            print("\nDefaulting to " + Highlighter("TBD").highlight() + " (type not detected).")
            return "TBD"


def analyze_title_style(title):
    """
    Analyze title style to suggest content type.
    
    Args:
        title: The document title (H1 heading)
        
    Returns:
        Suggested content type string or None
    """
    if not title:
        return None
        
    title = title.strip()
    
    # Remove title prefix (= or #) and clean up
    title = re.sub(r'^[=# ]+', '', title).strip()
    
    # Procedure patterns (gerund forms)
    gerund_patterns = [
        r'^(Creating|Installing|Configuring|Setting up|Building|Deploying|Managing|Updating|Upgrading)',
        r'^(Adding|Removing|Deleting|Enabling|Disabling|Starting|Stopping|Restarting)',
        r'^(Implementing|Establishing|Defining|Developing|Generating|Publishing)'
    ]
    
    for pattern in gerund_patterns:
        if re.match(pattern, title, re.IGNORECASE):
            return "PROCEDURE"
    
    # Reference patterns
    reference_patterns = [
        r'(reference|commands?|options?|parameters?|settings?|configuration)',
        r'(syntax|examples?|list of|table of|glossary)',
        r'(api|cli|command.?line)'
    ]
    
    for pattern in reference_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return "REFERENCE"
    
    # Assembly patterns (collection indicators)
    assembly_patterns = [
        r'(guide|tutorial|walkthrough|workflow)',
        r'(getting started|quick start|step.?by.?step)'
    ]
    
    for pattern in assembly_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return "ASSEMBLY"
    
    # Default to concept for other noun phrases
    return "CONCEPT"


def analyze_content_patterns(content):
    """
    Analyze content structure to suggest content type.
    
    Args:
        content: Full file content as string
        
    Returns:
        Suggested content type string or None
    """
    # Assembly indicators (most specific, check first)
    if re.search(r'include::', content):
        return "ASSEMBLY"
    
    # Procedure indicators
    procedure_patterns = [
        r'^\s*\d+\.\s',  # numbered steps
        r'^\.\s*Procedure\s*$',  # .Procedure section
        r'^\.\s*Prerequisites?\s*$',  # .Prerequisites section
        r'^\.\s*Verification\s*$',  # .Verification section
        r'^\s*\*\s+[A-Z][^.]*\.$'  # bullet points with imperative sentences ending in period
    ]
    
    procedure_count = 0
    for pattern in procedure_patterns:
        if re.search(pattern, content, re.MULTILINE):
            procedure_count += 1
    
    if procedure_count >= 2:  # Multiple procedure indicators
        return "PROCEDURE"
    
    # Reference indicators
    reference_patterns = [
        r'\|====',  # AsciiDoc tables
        r'^\w+::\s*$',  # definition lists
        r'^\[options="header"\]',  # table headers
        r'^\|\s*\w+\s*\|\s*\w+',  # table rows
    ]
    
    reference_count = 0
    for pattern in reference_patterns:
        if re.search(pattern, content, re.MULTILINE):
            reference_count += 1
    
    # Count definition lists (::)
    definition_count = len(re.findall(r'::\s*$', content, re.MULTILINE))
    if definition_count > 3 or reference_count >= 1:
        return "REFERENCE"
    
    # No clear patterns found
    return None


def get_document_title(lines):
    """
    Extract the document title (first H1 heading) from file lines.
    
    Args:
        lines: List of (text, ending) tuples from file
        
    Returns:
        Title string or None
    """
    for text, _ in lines:
        stripped = text.strip()
        if stripped.startswith('= '):
            return stripped[2:].strip()
        elif stripped.startswith('# '):
            return stripped[2:].strip()
    return None


def ensure_blank_line_below(lines, index):
    """
    Ensure there is a blank line (empty text) after the given index in lines.
    Args:
        lines: List of (text, ending) tuples
        index: Index of the content type attribute line
    Returns:
        Modified lines with a blank line after the attribute
    """
    # If the attribute is the last line, add a blank line
    if index == len(lines) - 1:
        lines.append(("", "\n"))
    # If the next line is not blank, insert a blank line
    elif lines[index + 1][0].strip() != "":
        lines.insert(index + 1, ("", "\n"))
    return lines


def process_content_type_file(filepath):
    """
    Process a single file for content type attributes.
    Overhauled: Only one :_mod-docs-content-type: attribute is allowed, always updated in-place.
    """
    filename = os.path.basename(filepath)
    print(f"\nChecking {Highlighter(filename).bold()}...")

    try:
        if not os.path.exists(filepath):
            print(f"  ❌ Error: File not found: {filepath}")
            print("=" * 40)
            return
        
        if not os.access(filepath, os.R_OK):
            print(f"  ❌ Error: Cannot read file: {filepath}")
            print("=" * 40)
            return
            
        lines = read_text_preserve_endings(filepath)
        if not lines:
            print(f"  ⚠️  Warning: File is empty: {filepath}")
            print("=" * 40)
            return
            
        # Detect existing content type attributes (including deprecated formats)
        existing_content_type, existing_index, attr_type = detect_existing_content_type(lines)
        
        # Find all content type attribute lines (current format only)
        ct_indices = [i for i, (text, _) in enumerate(lines)
                      if text.strip().startswith(":_mod-docs-content-type:") or 
                         text.strip().startswith("//:_mod-docs-content-type:")]
        
        # Handle existing attributes (current or deprecated)
        if existing_content_type is not None:
            i = existing_index
            text, ending = lines[i]
            
            # Convert deprecated formats to current format
            if attr_type == 'deprecated_content':
                text = text.replace(":_content-type:", ":_mod-docs-content-type:", 1)
            elif attr_type == 'deprecated_module':
                text = text.replace(":_module-type:", ":_mod-docs-content-type:", 1)
            elif text.strip().startswith("//:_mod-docs-content-type:"):
                # Uncomment if needed
                text = text.replace("//:_mod-docs-content-type:", ":_mod-docs-content-type:", 1)
            
            # Check if value is empty and prompt if needed
            value = text.split(":_mod-docs-content-type:", 1)[-1].strip()
            if not value:
                title = get_document_title(lines)
                full_content = '\n'.join([t for t, _ in lines])
                title_suggestion = analyze_title_style(title) if title else None
                content_suggestion = analyze_content_patterns(full_content)
                suggested_type = content_suggestion or title_suggestion
                value = prompt_user_for_content_type(suggested_type)
                if not value:
                    print(f"  → Skipped")
                    print("=" * 40)
                    return
            
            # Update the line with current format
            lines[i] = (f":_mod-docs-content-type: {value}", ending)
            
            # Remove any duplicate current format lines
            for j in sorted(ct_indices, reverse=True):
                if j != i:  # Don't remove the one we just updated
                    del lines[j]
            
            # Ensure blank line after
            lines = ensure_blank_line_below(lines, i)
            write_text_preserve_endings(filepath, lines)
            
            action = "Updated" if attr_type == 'current' else f"Converted from {attr_type}"
            print(f"  ✓ {action}: {Highlighter(value).success()}")
            print("=" * 40)
            return
        
        # Try filename-based detection
        filename_content_type = get_content_type_from_filename(filename)
        if filename_content_type:
            print(f"  💡 Detected from filename: {Highlighter(filename_content_type).highlight()}")
            # Add content type at the beginning
            lines.insert(0, (f":_mod-docs-content-type: {filename_content_type}", "\n"))
            lines = ensure_blank_line_below(lines, 0)
            write_text_preserve_endings(filepath, lines)
            print(f"  ✓ Added content type: {Highlighter(filename_content_type).success()}")
            print("=" * 40)
            return
        
        # Try smart content analysis
        print("  🔍 Analyzing file content...")
        # Get document title and full content for analysis
        title = get_document_title(lines)
        full_content = '\n'.join([text for text, _ in lines])
        # Analyze title style and content patterns
        title_suggestion = analyze_title_style(title) if title else None
        content_suggestion = analyze_content_patterns(full_content)
        # Choose the most specific suggestion
        suggested_type = content_suggestion or title_suggestion
        if suggested_type:
            print(f"  💭 Analysis suggests: {Highlighter(suggested_type).highlight()}")
            if title:
                print(f"     Based on title: '{title[:50]}{'...' if len(title) > 50 else ''}'")
        # Prompt user with smart pre-selection
        content_type = prompt_user_for_content_type(suggested_type)
        if content_type:
            lines.insert(0, (f":_mod-docs-content-type: {content_type}", "\n"))
            lines = ensure_blank_line_below(lines, 0)
            write_text_preserve_endings(filepath, lines)
            print(f"  ✓ Added content type: {Highlighter(content_type).success()}")
        else:
            print(f"  → Skipped")
        print("=" * 40)

    except PermissionError:
        print(f"  ❌ Error: Permission denied: {filepath}")
        print("=" * 40)
    except UnicodeDecodeError:
        print(f"  ❌ Error: Cannot decode file (not UTF-8): {filepath}")
        print("=" * 40)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("=" * 40)


def main(args):
    """Main function for the ContentType plugin."""
    process_adoc_files(args, process_content_type_file)


def register_subcommand(subparsers):
    """Register this plugin as a subcommand."""
    if not is_plugin_enabled("ContentType"):
        return  # Plugin is disabled, don't register
    parser = subparsers.add_parser("ContentType", help=__description__)
    common_arg_parser(parser)
    parser.set_defaults(func=main)
