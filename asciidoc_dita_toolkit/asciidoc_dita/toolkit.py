"""
toolkit.py - Unified CLI for AsciiDoc DITA scripts

This script provides a single entry point for running various AsciiDoc DITA checks and fixers as subcommands.
It dynamically discovers plugins in the 'plugins' directory. Each plugin must define a 'register_subcommand(subparsers)' function.
"""

import argparse
import importlib
import importlib.metadata
import os
import sys

PLUGIN_DIR = os.path.join(os.path.dirname(__file__), "plugins")


def discover_plugins():
    """
    Dynamically discover and import all plugin modules in the plugins directory.

    Returns:
        List of plugin module names
    """
    plugins = []
    if not os.path.isdir(PLUGIN_DIR):
        return plugins

    for fname in os.listdir(PLUGIN_DIR):
        if fname.endswith(".py") and not fname.startswith("_"):
            modname = fname[:-3]
            plugins.append(modname)

    return plugins


def print_plugin_list():
    """Print a list of all available plugins with their descriptions."""
    print("Available plugins:")
    plugins = discover_plugins()

    for modname in plugins:
        try:
            module = importlib.import_module(
                f".plugins.{modname}", package="asciidoc_dita_toolkit.asciidoc_dita"
            )
            desc = getattr(module, "__description__", None) or module.__doc__ or ""
            desc = desc.strip().split("\n")[0] if desc else ""
            print(f"  {modname:20} {desc}")
        except Exception as e:
            print(f"  {modname:20} (error loading plugin: {e})")


def main():
    """Main entry point for the AsciiDoc DITA toolkit."""
    parser = argparse.ArgumentParser(
        description="AsciiDoc DITA Toolkit - Process and validate AsciiDoc files for DITA publishing"
    )
    parser.add_argument(
        "--list-plugins",
        action="store_true",
        help="List all available plugins and their descriptions",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show the version of the AsciiDoc DITA Toolkit and exit",
    )
    subparsers = parser.add_subparsers(dest="command", required=False)

    # Discover and register all plugins
    plugins = discover_plugins()
    plugin_modules = []

    for modname in plugins:
        try:
            module = importlib.import_module(
                f".plugins.{modname}", package="asciidoc_dita_toolkit.asciidoc_dita"
            )
            if hasattr(module, "register_subcommand"):
                module.register_subcommand(subparsers)
                plugin_modules.append(module)
            else:
                print(
                    f"Warning: Plugin '{modname}' missing register_subcommand function",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"Error loading plugin '{modname}': {e}", file=sys.stderr)

    args = parser.parse_args()

    if args.version:
        version = importlib.metadata.version("asciidoc-dita-toolkit")
        print(f"asciidoc-dita-toolkit {version}")
        sys.exit(0)

    if args.list_plugins:
        print_plugin_list()
        sys.exit(0)

    # Each plugin's register_subcommand sets a 'func' attribute
    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
