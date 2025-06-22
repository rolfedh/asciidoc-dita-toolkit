# Contributing to AsciiDoc DITA Toolkit

Thank you for your interest in contributing! This guide is for developers and maintainers.

## Project Structure

- **`asciidoc_dita_toolkit/`**: Main Python package (PyPI distribution)
  - `asciidoc_toolkit.py`: CLI entry point (use as a module)
  - `file_utils.py`: Shared file and argument utilities
  - `plugins/`: Plugin scripts (each plugin is a subcommand)
- **`tests/`**: Automated tests and test fixtures
- **`docs/`**: Project documentation (including this file)
- **`requirements.txt`**: Development dependencies
- **`pyproject.toml`**: Packaging and metadata

## Getting Started

1. **Fork and clone the repository**
   ```sh
   git clone https://github.com/<your-org>/asciidoc-dita-toolkit.git
   cd asciidoc-dita-toolkit
   ```
2. **(Optional) Set up a virtual environment**
   ```sh
   python3 -m venv .venv
   . .venv/bin/activate
   python3 -m pip install -r requirements.txt
   ```
3. **Install in editable mode for development**
   ```sh
   python3 -m pip install -e .
   ```

## Branch Protection Rules

We've enabled branch protections on the `main` branch to help maintain a clean and stable codebase:

- **Pull requests are now required**: All changes must come through a PR—no direct commits to `main`.
- **PRs require approval**: At least one review and no outstanding change requests are needed before merging.
- **Status checks must pass**: Any required checks (like CI tests) must succeed before a PR can be merged.
- **Linear history enforced**: We'll be using rebase or squash merges to avoid merge commits in `main`.
- **No bypassing**: These rules apply to everyone, including admins.

If you have any questions or run into issues with these protections, please reach out to the maintainers.

## Adding Plugins
- Add new plugins to `asciidoc_dita_toolkit/plugins/` (e.g., `MyPlugin.py`).
- Each plugin must have a `register_subcommand` function and a clear `__description__`.
- Follow the structure and docstring conventions used in `EntityReference.py`.
- Plugins are automatically discovered as CLI subcommands.

## Writing and Running Tests
- Add or update test files in `tests/` (prefix with `test_`, e.g., `test_MyPlugin.py`).
- Use `unittest` and the shared testkit (`asciidoc_testkit.py`).
- Place test fixtures in `tests/fixtures/<PluginName>/`.
- Run all tests:
  ```sh
  python3 -m unittest discover -s tests
  ```

## CI Integration
- Ensure `.github/workflows/ci.yml` runs all tests and downloads fixtures if needed.
- All pull requests must pass CI before merging.

## Review and Merge
- Open a pull request for your changes.
- Request review from maintainers.
- Address feedback, ensure CI passes, and merge when approved.

...
## Publishing a New Release to PyPI

To have the GitHub Actions workflow build and upload the package to PyPI using the `PYPI_API_TOKEN` secret:

1. **Update the version** in `pyproject.toml`.
2. **Commit and push** your changes:
   ```sh
   git add pyproject.toml
   git commit -m "Bump version to <new-version>"
   git push
   ```
3. **Tag the release and push the tag:**
   ```sh
   git tag v<new-version>  # Example: v0.1.3
   git push origin v<new-version>
   ```
4. GitHub Actions will build and upload the package to PyPI automatically.

## Troubleshooting if the tagging gets ahead of the version:
   ```
   git tag -d v0.1.3
   git tag v0.1.3
   git push --force origin v0.1.3
   ```

**Manual publishing (alternative):**
1. Build the package:
   ```sh
   python3 -m pip install --upgrade build twine
   python3 -m build
   ```
2. Upload to PyPI:
   ```sh
   python3 -m twine upload dist/*
   ```

See the main README for more details.

## Toolkit Components Overview

* **`asciidoc_toolkit.py`**: CLI entry point, discovers and runs plugins.
* **`plugins/`**: Individual plugin scripts for transformations/validations.
* **`file_utils.py`**: Shared file/argument utilities.
* **`tests/`**: Automated tests and fixtures.
* **`requirements.txt`**: Python dependencies for development.
* **`README.md`**: End-user setup, usage, and project overview.

## Why contribute?

- Modern Python and robust testing practices
- Improve publishing workflows for AsciiDoc and DITA
- Active review and maintenance
