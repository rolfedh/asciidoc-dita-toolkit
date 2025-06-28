#!/usr/bin/env python3
import re
import os
import sys
import html
import argparse

# Helper to slugify rule names for persistent ids
def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

def extract_tables(md_text):
    # Find the section under '## Available rules'
    rules_section = re.split(r"^## Available rules", md_text, flags=re.MULTILINE)[-1]
    # Updated regex: allow for any text (including newlines) between heading and table
    pattern = re.compile(r"### (Errors|Warnings|Suggestions)\n(?:.*?\n)*?(\| Vale Rule \| Explanation \|(?:\n\|.*)+)", re.MULTILINE)
    tables = []
    for match in pattern.finditer(rules_section):
        severity = match.group(1)
        table_md = match.group(2)
        # Parse table rows
        rows = [r.strip() for r in table_md.strip().split("\n") if r.strip().startswith("|")]
        # Remove header and separator
        if len(rows) >= 2:
            rows = rows[2:]
        entries = []
        for row in rows:
            cols = [c.strip() for c in row.strip("|").split("|")]
            if len(cols) == 2:
                rule, explanation = cols
                entries.append((rule, explanation))
        tables.append((severity, entries))
    return tables

def generate_html(tables):
    html_parts = [
        "<html>",
        "<head><meta charset='utf-8'><title>AsciiDocDITA Vale Rules</title></head>",
        "<body>",
        "<h1>AsciiDocDITA Vale Rules</h1>"
    ]
    for severity, entries in tables:
        html_parts.append(f"<h2>{html.escape(severity)}</h2>")
        html_parts.append("<table border='1' cellspacing='0' cellpadding='4'>")
        html_parts.append("<tr><th>Vale Rule</th><th>Explanation</th></tr>")
        for rule, explanation in entries:
            rule_id = slugify(rule)
            html_parts.append(
                f"<tr id='{rule_id}'><td>{html.escape(rule)}</td><td>{html.escape(explanation)}</td></tr>"
            )
        html_parts.append("</table>")
    html_parts.append("</body></html>")
    return "\n".join(html_parts)

def main():
    parser = argparse.ArgumentParser(
        description="Generate an HTML report of Vale rules from a Markdown file."
    )
    parser.add_argument(
        "input_file", help="Path to the input Markdown file (e.g., README.md)."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output HTML file. Defaults to replacing the input file's extension with .html.",
    )
    args = parser.parse_args()

    input_path = args.input_file
    output_path = args.output
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".html"

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            md_text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    tables = extract_tables(md_text)
    html_text = generate_html(tables)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_text)
    print(f"HTML file generated at {output_path}")


if __name__ == "__main__":
    main()
