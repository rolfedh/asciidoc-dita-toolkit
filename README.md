# AsciiDoc DITA Toolkit

[![PyPI version](https://badge.fury.io/py/asciidoc-dita-toolkit.svg)](https://badge.fury.io/py/asciidoc-dita-toolkit)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Scripts to review and fix AsciiDoc content for DITA-based publishing workflows, based on rules from the [asciidoctor-dita-vale](https://github.com/jhradilek/asciidoctor-dita-vale) project.

## 🚀 Resources

- [PyPI: asciidoc-dita-toolkit](https://pypi.org/project/asciidoc-dita-toolkit/)
- [GitHub repository](https://github.com/rolfedh/asciidoc-dita-toolkit)
- [Documentation](https://github.com/rolfedh/asciidoc-dita-toolkit/blob/main/docs/)
- [Contributing Guide](https://github.com/rolfedh/asciidoc-dita-toolkit/blob/main/docs/CONTRIBUTING.md)

## 📖 What is this?

The AsciiDoc DITA Toolkit is a command-line tool for technical writers and editors. It helps you:

- **Find and fix** common issues in `.adoc` files before publishing
- **Apply automated checks** and transformations using a plugin system
- **Ensure consistency** across large documentation projects
- **Integrate** with your existing documentation workflow

## 📦 Installation

### Option 1: Container (No Python Required)

Use Docker containers if you prefer not to install Python dependencies locally, or need consistent environments across teams:

```sh
# Production use (smaller, optimized)
docker run --rm -v $(pwd):/workspace rolfedh/asciidoc-dita-toolkit-prod:latest --help

# Development use (includes dev tools)
docker run --rm -v $(pwd):/workspace rolfedh/asciidoc-dita-toolkit:latest --help

# GitHub Container Registry (alternative)
docker run --rm -v $(pwd):/workspace ghcr.io/rolfedh/asciidoc-dita-toolkit:latest --help
```

**Benefits of container approach:**

- No need to install Python or manage dependencies
- Consistent environment across different systems
- Easy to use in CI/CD pipelines
- Automatic cleanup after each run

### Option 2: PyPI

Install the toolkit using pip:

```sh
python3 -m pip install asciidoc-dita-toolkit

# Test the installation
asciidoc-dita-toolkit --help

# Launch the GUI (recommended for new users)
asciidoc-dita-toolkit-gui
```

### Upgrading

**Container:**

```sh
# Production image (recommended for most users)
docker pull rolfedh/asciidoc-dita-toolkit-prod:latest

# Development image (includes dev tools)
docker pull rolfedh/asciidoc-dita-toolkit:latest
```

**PyPI:**

```sh
python3 -m pip install --upgrade asciidoc-dita-toolkit
```

### Requirements

- Python 3.7 or newer
- No external dependencies (uses only Python standard library)

## 🔧 Usage

### GUI Interface (Recommended for New Users)

For an intuitive, dialog-based interface, use the GUI:

```sh
asciidoc-dita-toolkit-gui
```

The GUI provides:
- **Plugin selection** - Choose from available plugins with descriptions
- **Easy configuration** - Browse for files/directories, set options with checkboxes
- **Multiple modes** - Review, Interactive, Auto, and Guided modes (when supported)
- **Real-time results** - See output and progress in an integrated results panel
- **Test file management** - Load sample test files to experiment with

**Benefits of the GUI:**
- No need to remember command-line syntax
- Visual feedback and error messages
- Perfect for learning how the tools work
- Test files included for experimentation

**System Requirements for GUI:**
- Python with tkinter support (included with most Python installations)
- On Linux: may need to install `python3-tk` package
- Works on Windows, macOS, and Linux

### Command Line Interface

For automation, scripting, or advanced usage:

### List available plugins

```sh
asciidoc-dita-toolkit --list-plugins
```

### Run a plugin

```sh
asciidoc-dita-toolkit <plugin> [options]
```

- `<plugin>`: Name of the plugin to run (e.g., `EntityReference`, `ContentType`)
- `[options]`: Plugin-specific options (e.g., `-f` for a file, `-r` for recursive)

### Common Options

All plugins support these options:

- `-f FILE` or `--file FILE`: Process a specific file
- `-r` or `--recursive`: Process all .adoc files recursively in the current directory
- `-d DIR` or `--directory DIR`: Specify the root directory to search (default: current directory)

### 📝 Examples

#### Fix HTML entity references in a file

```sh
asciidoc-dita-toolkit EntityReference -f path/to/file.adoc
```

#### Add content type labels to all files recursively

```sh
asciidoc-dita-toolkit ContentType -r
```

#### Process all .adoc files in a specific directory

```sh
asciidoc-dita-toolkit EntityReference -d /path/to/docs -r
```

### Container Usage

If using the container version, all commands work the same but are prefixed with the Docker run command:

```sh
# List plugins
docker run --rm rolfedh/asciidoc-dita-toolkit-prod:latest --list-plugins

# Fix entity references in current directory
docker run --rm -v $(pwd):/workspace rolfedh/asciidoc-dita-toolkit-prod:latest EntityReference -r

# Add content type labels to a specific file
docker run --rm -v $(pwd):/workspace rolfedh/asciidoc-dita-toolkit-prod:latest ContentType -f docs/myfile.adoc

# Interactive shell for development (use dev image)
docker run --rm -it -v $(pwd):/workspace rolfedh/asciidoc-dita-toolkit:latest /bin/bash
```

**Container command breakdown:**

- `docker run --rm` - Run and automatically remove container when done
- `-v $(pwd):/workspace` - Mount current directory as `/workspace` in container
- `rolfedh/asciidoc-dita-toolkit-prod:latest` - The production container image (recommended)
- Everything after the image name works exactly like the PyPI version

**Tip:** Create a shell alias to simplify container usage:

```sh
alias asciidoc-dita-toolkit='docker run --rm -v $(pwd):/workspace rolfedh/asciidoc-dita-toolkit-prod:latest'
```

Then use it exactly like the PyPI version:

```sh
asciidoc-dita-toolkit --list-plugins
asciidoc-dita-toolkit EntityReference -r
```

### 🔌 Available Plugins

| Plugin | Description | Example Usage |
|--------|-------------|---------------|
| `EntityReference` | Replace unsupported HTML character entity references with AsciiDoc attribute references | `asciidoc-dita-toolkit EntityReference -f file.adoc` |
| `ContentType` | Add `:_mod-docs-content-type:` labels where missing, based on filename | `asciidoc-dita-toolkit ContentType -r` |

> **📋 Technical Details**: For plugin internals and supported entity mappings, see [docs/asciidoc-dita-toolkit.md](docs/asciidoc-dita-toolkit.md).

## 🔍 Troubleshooting

- **Python Version**: Make sure you are using Python 3.7 or newer
- **Installation Issues**: Try upgrading pip: `python3 -m pip install --upgrade pip`
- **Development Setup**: If you need to use a local clone, see the [contributor guide](docs/CONTRIBUTING.md)
- **Plugin Errors**: Use `-v` or `--verbose` flag for detailed error information

## 📚 Related Resources

- **[`asciidoctor-dita-vale`](https://github.com/jhradilek/asciidoctor-dita-vale)**: Vale style rules and test fixtures for validating AsciiDoc content

## 🤝 Contributing

Want to add new plugins or help improve the toolkit?

- Read our [Contributing Guide](docs/CONTRIBUTING.md)
- Follow the [Plugin Development Pattern](docs/PLUGIN_DEVELOPMENT_PATTERN.md) for new plugins
- Check out [open issues](https://github.com/rolfedh/asciidoc-dita-toolkit/issues)
- See our [Security Policy](SECURITY.md) for reporting vulnerabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
