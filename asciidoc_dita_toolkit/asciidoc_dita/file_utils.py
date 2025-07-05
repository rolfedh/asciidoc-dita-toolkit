"""
file_utils.py - Shared utilities for AsciiDoc file processing scripts.

This module provides reusable functions for:
- Discovering .adoc files in a directory (optionally recursively), always ignoring symlinks.
- Reading and writing text files while preserving original line endings for each line.
- Validating .adoc files (extension, file type, not a symlink).
- Providing a common argument parser for CLI scripts.
- Batch processing of .adoc files using a user-supplied processing function.

Intended for use by all scripts in this repository to avoid code duplication and ensure consistent file handling.
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime

# Configure logging (implements improvement #4 from issue #87)
logger = logging.getLogger(__name__)

# Environment variable for non-interactive config selection (improvement #1 from issue #87)
ADT_CONFIG_CHOICE_ENV = "ADT_CONFIG_CHOICE"

# Regex to split lines and preserve their original line endings
LINE_SPLITTER = re.compile(rb"(.*?)(\r\n|\r|\n|$)")


def find_adoc_files(root, recursive):
    """
    Find all .adoc files in the given directory (optionally recursively), ignoring symlinks.

    Args:
        root: Root directory to search
        recursive: Whether to search recursively

    Returns:
        List of file paths
    """
    adoc_files = []

    # Validate root directory using consolidated validation
    is_valid, result = validate_directory_path(root, require_exists=True)
    if not is_valid:
        logger.warning(f"Directory validation failed: {result}")
        return adoc_files

    try:
        if recursive:
            for dirpath, dirnames, filenames in os.walk(root):
                for filename in filenames:
                    if filename.endswith(".adoc"):
                        fullpath = os.path.join(dirpath, filename)
                        if not os.path.islink(fullpath):
                            adoc_files.append(fullpath)
        else:
            for filename in os.listdir(root):
                if filename.endswith(".adoc"):
                    fullpath = os.path.join(root, filename)
                    if not os.path.islink(fullpath):
                        adoc_files.append(fullpath)
    except PermissionError as e:
        logger.warning(f"Permission denied accessing directory '{root}': {e}")
    except OSError as e:
        logger.warning(f"Could not access directory '{root}': {e}")
    except Exception as e:
        logger.warning(f"Unexpected error processing directory '{root}': {e}")

    return adoc_files


def read_text_preserve_endings(filepath):
    """
    Read a file as bytes, split into lines preserving original line endings, and decode as UTF-8.

    Args:
        filepath: Path to the file to read

    Returns:
        List of (text, ending) tuples, where 'text' is the line content and 'ending' is the original line ending.
    """
    with open(filepath, "rb") as f:
        content = f.read()

    lines = []
    for match in LINE_SPLITTER.finditer(content):
        text = match.group(1).decode("utf-8")
        ending = match.group(2).decode("utf-8") if match.group(2) else ""
        lines.append((text, ending))
        if not ending:
            break

    return lines


def write_text_preserve_endings(filepath, lines):
    """
    Write a list of (text, ending) tuples to a file, preserving original line endings.

    Args:
        filepath: Path to the file to write
        lines: List of (text, ending) tuples, where 'ending' is the original line ending (e.g., '\n', '\r\n', or '').
    """
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        for text, ending in lines:
            f.write(text + ending)


def common_arg_parser(parser):
    """
    Add standard options to the supplied parser:
    -d / --directory: Root directory to search (default: current directory)
    -r / --recursive: Search subdirectories recursively
    -f / --file: Scan only the specified .adoc file

    Args:
        parser: ArgumentParser instance to add arguments to
    """
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument(
        "-d",
        "--directory",
        type=str,
        default=".",
        help="Root directory to search (default: current directory)",
    )
    sources.add_argument("-f", "--file", type=str, help="Scan only the specified .adoc file")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Search subdirectories recursively",
    )


def is_valid_adoc_file(filepath):
    """
    Check if the given path is a regular .adoc file (not a symlink).

    Args:
        filepath: Path to check

    Returns:
        True if the path is a valid .adoc file, False otherwise
    """
    return os.path.isfile(filepath) and filepath.endswith(".adoc") and not os.path.islink(filepath)


def process_adoc_files(args, process_file_func):
    """
    Batch processing pattern for .adoc files with optional directory configuration:
    - If --file is given and valid, process only that file.
    - Otherwise, find all .adoc files using directory configuration if available,
      or fall back to legacy behavior (recursively if requested) in the specified directory.

    Args:
        args: Parsed command line arguments (must have 'file', 'directory', 'recursive' attributes)
        process_file_func: Function that takes a file path and processes it
    """
    if args.file:
        if is_valid_adoc_file(args.file):
            process_file_func(args.file)
        else:
            logger.error(f"{args.file} is not a valid .adoc file or is a symlink.")
    else:
        # Try to load directory configuration
        config = load_directory_config()
        directory_path = getattr(args, "directory", ".")
        
        if config:
            # Use configuration-aware file discovery
            logger.info("Using directory configuration")
            adoc_files = get_filtered_adoc_files(directory_path, config)
            if adoc_files:
                directories = apply_directory_filters(directory_path, config)
                excluded_count = len(config.get('excludeDirs', []))
                logger.info(f"Processing {len(directories)} director{'y' if len(directories) == 1 else 'ies'}" + 
                           (f", excluding {excluded_count}" if excluded_count > 0 else ""))
                logger.info(f"Found {len(adoc_files)} .adoc file{'s' if len(adoc_files) != 1 else ''} to process")
            else:
                logger.warning("No .adoc files found in configured directories")
        else:
            # Legacy behavior: process all files in directory
            adoc_files = find_adoc_files(
                directory_path, getattr(args, "recursive", False)
            )
        
        for filepath in adoc_files:
            process_file_func(filepath)

# Helper functions for path operations
def _is_subpath(child_path, parent_path):
    """
    Check if child_path is a subpath of parent_path.
    
    Args:
        child_path: Path that might be a child
        parent_path: Path that might be the parent
    
    Returns:
        True if child_path is under parent_path, False otherwise
    """
    try:
        child_path = os.path.abspath(child_path)
        parent_path = os.path.abspath(parent_path)
        
        # Use os.path.commonpath for safer comparison
        try:
            common = os.path.commonpath([child_path, parent_path])
            return common == parent_path
        except ValueError:
            # Paths are on different drives (Windows) or other issues
            return False
    except (OSError, ValueError):
        return False


def _normalize_path_for_comparison(path):
    """
    Normalize a path for safe comparison operations.
    
    Args:
        path: Path to normalize
    
    Returns:
        Normalized absolute path
    """
    return os.path.abspath(os.path.normpath(path))


# Directory Configuration Support
def is_plugin_enabled(plugin_name):
    """
    Check if a plugin is enabled. For now, all plugins are enabled by default.
    This is a placeholder for future plugin configurator implementation.
    
    Args:
        plugin_name: Name of the plugin to check
    
    Returns:
        True if plugin is enabled, False otherwise
    """
    # TODO: Implement actual plugin configuration system
    # For MVP, DirectoryConfig and ContentType are disabled by default (preview stage)
    if plugin_name == "DirectoryConfig":
        return os.environ.get("ADT_ENABLE_DIRECTORY_CONFIG", "false").lower() == "true"
    if plugin_name == "ContentType":
        return os.environ.get("ADT_ENABLE_CONTENT_TYPE", "false").lower() == "true"
    return True


def load_config_file(config_path):
    """
    Load configuration from a JSON file with enhanced validation (improvement #3 from issue #87).
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        Dictionary with configuration data or None if file doesn't exist/invalid
    """
    expanded_path = os.path.expanduser(config_path)
    if not os.path.exists(expanded_path):
        return None
    
    try:
        with open(expanded_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Enhanced validation (improvement #3 from issue #87)
        if not _validate_config_structure(config):
            logger.warning(f"Invalid configuration file format in {expanded_path}")
            return None
        
        return config
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load configuration from {expanded_path}: {e}")
        return None


def _validate_config_structure(config):
    """
    Enhanced configuration validation with type checking (improvement #3 from issue #87).
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        True if configuration is valid, False otherwise
    """
    if not isinstance(config, dict):
        return False
    
    required_fields = ['version', 'repoRoot', 'includeDirs', 'excludeDirs', 'lastUpdated']
    if not all(field in config for field in required_fields):
        return False
    
    # Type validation (improvement #3 from issue #87)
    if not isinstance(config.get('includeDirs'), list):
        return False
    if not isinstance(config.get('excludeDirs'), list):
        return False
    if not isinstance(config.get('repoRoot'), str):
        return False
    if not isinstance(config.get('version'), str):
        return False
    if not isinstance(config.get('lastUpdated'), str):
        return False
    
    # Validate directory paths in lists
    for dir_list in [config['includeDirs'], config['excludeDirs']]:
        if not all(isinstance(d, str) for d in dir_list):
            return False
    
    return True


def save_config_file(config_path, config_data):
    """
    Save configuration to a JSON file.
    
    Args:
        config_path: Path to save the configuration file
        config_data: Dictionary with configuration data
    
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        expanded_path = os.path.expanduser(config_path)
        os.makedirs(os.path.dirname(expanded_path), exist_ok=True)
        
        # Update timestamp
        config_data['lastUpdated'] = datetime.now().isoformat()
        
        with open(expanded_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        
        return True
    except (IOError, OSError) as e:
        logger.error(f"Could not save configuration to {expanded_path}: {e}")
        return False


def prompt_user_to_choose_config(local_config, home_config):
    """
    Prompt user to choose between local and home configuration files.
    Supports non-interactive mode via environment variable (improvement #1 from issue #87).
    
    Args:
        local_config: Configuration data from local .adtconfig.json
        home_config: Configuration data from ~/.adtconfig.json
    
    Returns:
        Selected configuration data
    """
    # Non-interactive mode for CI/automation (improvement #1 from issue #87)
    env_choice = os.environ.get(ADT_CONFIG_CHOICE_ENV)
    if env_choice:
        if env_choice == "1" or env_choice.lower() == "local":
            logger.info("Using local configuration (set via ADT_CONFIG_CHOICE)")
            return local_config
        elif env_choice == "2" or env_choice.lower() == "home":
            logger.info("Using home configuration (set via ADT_CONFIG_CHOICE)")
            return home_config
        else:
            logger.warning(f"Invalid ADT_CONFIG_CHOICE value: {env_choice}, falling back to interactive mode")
    
    # Interactive mode
    print("Multiple configuration files found:")
    print(f"[1] Local:  ./.adtconfig.json (last updated: {local_config.get('lastUpdated', 'unknown')})")
    print(f"[2] Home:   ~/.adtconfig.json (last updated: {home_config.get('lastUpdated', 'unknown')})")
    
    # Preselect most recent
    local_time = local_config.get('lastUpdated', '1970-01-01T00:00:00Z')
    home_time = home_config.get('lastUpdated', '1970-01-01T00:00:00Z')
    default_choice = "1" if local_time >= home_time else "2"
    
    while True:
        choice = input(f"Select configuration to use [{default_choice}]: ").strip()
        if not choice:
            choice = default_choice
        
        if choice == "1":
            return local_config
        elif choice == "2":
            return home_config
        else:
            print("Please enter 1 or 2")


def load_directory_config():
    """
    Load directory configuration with proper fallback chain.
    
    Returns:
        Configuration dictionary or None if no configuration found/plugin disabled
    """
    if not is_plugin_enabled("DirectoryConfig"):
        return None
    
    # Check current directory first
    local_config = load_config_file("./.adtconfig.json")
    home_config = load_config_file("~/.adtconfig.json")
    
    if local_config and home_config:
        return prompt_user_to_choose_config(local_config, home_config)
    
    return local_config or home_config


def apply_directory_filters(base_path, config):
    """
    Apply directory configuration filters to determine which directories to process.
    
    Args:
        base_path: Base directory path specified by user
        config: Directory configuration dictionary
    
    Returns:
        List of directories to process
    """
    if not config:
        return [base_path]
    
    repo_root = config.get('repoRoot', base_path)
    include_dirs = config.get('includeDirs', [])
    exclude_dirs = config.get('excludeDirs', [])
    
    # If base_path is specified and is within repo_root, honor it
    base_path = os.path.abspath(base_path)
    repo_root = os.path.abspath(os.path.expanduser(repo_root))
    
    # Start with the specified base_path
    dirs_to_process = [base_path]
    
    # If include_dirs is specified, only process directories that match the include pattern
    if include_dirs:
        # Check if base_path intersects with any included directories
        intersecting_dirs = []
        for include_dir in include_dirs:
            full_include_path = os.path.abspath(os.path.join(repo_root, include_dir))
            # Check if paths overlap (using proper path comparison)
            if (_is_subpath(full_include_path, base_path) or 
                _is_subpath(base_path, full_include_path) or
                base_path == full_include_path):
                intersecting_dirs.append(full_include_path)
        
        if intersecting_dirs:
            dirs_to_process = intersecting_dirs
        else:
            # No intersection - warn but still process the requested directory
            logger.warning(f"Specified directory '{base_path}' is not in included directories")
    
    # Filter out excluded directories
    if exclude_dirs:
        filtered_dirs = []
        for dir_path in dirs_to_process:
            excluded = False
            for exclude_dir in exclude_dirs:
                full_exclude_path = os.path.abspath(os.path.join(repo_root, exclude_dir))
                if _is_subpath(dir_path, full_exclude_path):
                    excluded = True
                    logger.warning(f"Directory '{dir_path}' is excluded by configuration")
                    break
            if not excluded:
                filtered_dirs.append(dir_path)
        dirs_to_process = filtered_dirs
    
    # Filter to only existing directories
    existing_dirs = [d for d in dirs_to_process if os.path.isdir(d)]
    
    # Warn about missing directories
    missing_dirs = set(dirs_to_process) - set(existing_dirs)
    if missing_dirs:
        for missing_dir in missing_dirs:
            logger.warning(f"Configured directory does not exist: {missing_dir}")
    
    return existing_dirs if existing_dirs else [base_path]


def get_filtered_adoc_files(directory_path, config):
    """
    Get .adoc files with directory configuration filtering applied.
    Uses optimized duplicate removal (improvement #2 from issue #87).
    
    Args:
        directory_path: Base directory to search
        config: Directory configuration dictionary
    
    Returns:
        List of .adoc file paths
    """
    directories = apply_directory_filters(directory_path, config)
    all_files = []
    
    for directory in directories:
        files = find_adoc_files(directory, recursive=True)  # Always recursive for configured directories
        all_files.extend(files)
    
    # Optimized duplicate removal (improvement #2 from issue #87)
    return list(dict.fromkeys(all_files))

# Directory validation utilities
def sanitize_directory_path(directory_path):
    """
    Sanitize directory path to prevent directory traversal attacks.
    
    Args:
        directory_path: Directory path to sanitize
    
    Returns:
        Sanitized path or None if path is dangerous
    """
    if not directory_path:
        return None
    
    # Remove dangerous patterns
    dangerous_patterns = ["../", "..\\"]
    sanitized = directory_path.strip()
    
    # Check for directory traversal attempts
    if any(pattern in sanitized for pattern in dangerous_patterns):
        return None
    
    # Check for null bytes or other control characters
    if '\x00' in sanitized or any(ord(c) < 32 for c in sanitized if c not in '\t\n\r'):
        return None
    
    # Normalize path separators and remove redundant elements
    sanitized = os.path.normpath(sanitized)
    
    # Additional check after normalization for traversal attempts
    if '..' in sanitized.split(os.sep):
        return None
    
    return sanitized


def validate_directory_path(directory_path, base_path=None, require_exists=True):
    """
    Validate that a directory path is safe and optionally exists.
    
    Args:
        directory_path: Directory path to validate
        base_path: Base directory for relative paths (optional)
        require_exists: Whether the directory must exist
    
    Returns:
        Tuple of (is_valid: bool, result: str) where result is either the validated path or error message
    """
    if not directory_path:
        return False, "Directory path cannot be empty"
    
    # Sanitize input first
    sanitized_path = sanitize_directory_path(directory_path)
    if sanitized_path is None:
        return False, f"Invalid directory path (security check failed): {directory_path}"
    
    # Convert to absolute path relative to base_path if provided
    if base_path and not os.path.isabs(sanitized_path):
        full_path = os.path.join(base_path, sanitized_path)
    else:
        full_path = sanitized_path
    
    # Normalize and resolve the path
    try:
        full_path = os.path.realpath(full_path)
    except (OSError, ValueError) as e:
        return False, f"Cannot resolve path: {e}"
    
    # Security check: ensure the resolved path is within base_path if provided
    if base_path:
        try:
            base_path = os.path.realpath(base_path)
            if not _is_subpath(full_path, base_path) and full_path != base_path:
                return False, f"Directory must be within base path: {full_path}"
        except (OSError, ValueError) as e:
            return False, f"Cannot validate base path: {e}"
    
    if require_exists:
        if not os.path.exists(full_path):
            return False, f"Directory does not exist: {full_path}"
        
        if not os.path.isdir(full_path):
            return False, f"Path is not a directory: {full_path}"
    
    return True, full_path
