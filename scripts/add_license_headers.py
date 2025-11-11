#!/usr/bin/env python3
# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add Apache 2.0 license headers to source files."""

from pathlib import Path

# License header templates for different file types
PYTHON_HEADER = """# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

SHELL_HEADER = """# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

YAML_HEADER = """# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

# Files/directories to skip
SKIP_PATTERNS = {
    ".git/",  # More specific to avoid matching .github
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    ".docusaurus",
    "yarn.lock",
    "package-lock.json",
    "uv.lock",
    ".DS_Store",
    "LICENSE",
    "README.md",
    ".gitignore",
    ".python-version",
    "pyproject.toml",
    "tsconfig.json",
    "package.json",
    "sidebars.ts",
    "docusaurus.config.ts",
    ".dockerignore",
    "cdk.json",
    "requirements.txt",
}

# File extensions that should have headers
HEADER_EXTENSIONS = {
    ".py": PYTHON_HEADER,
    ".sh": SHELL_HEADER,
    ".yml": YAML_HEADER,
    ".yaml": YAML_HEADER,
}


def should_skip(path: Path) -> bool:
    """Check if a file/directory should be skipped."""
    path_str = str(path)
    
    # Skip by pattern
    for pattern in SKIP_PATTERNS:
        if pattern in path_str:
            return True
    
    # Skip if in data directory
    if "/data/" in path_str or path_str.startswith("data/"):
        return True
    
    # Skip markdown files (documentation)
    if path.suffix == ".md":
        return True
    
    # Skip JSON files
    if path.suffix == ".json":
        return True
    
    # Skip TypeScript/JavaScript files (different license header style)
    if path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return True
    
    return False


def has_license_header(content: str) -> bool:
    """Check if file already has a license header."""
    # Check for Apache License or Copyright in first 500 chars
    header_section = content[:500]
    return (
        "Apache License" in header_section
        or "Copyright" in header_section
        or "Licensed under the Apache License" in header_section
    )


def add_header_to_file(filepath: Path, header: str) -> bool:
    """Add license header to a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"  Skipping {filepath} (read error: {e})")
        return False
    
    if not content.strip():
        print(f"  Skipping {filepath} (empty file)")
        return False
    
    if has_license_header(content):
        print(f"  Already has header: {filepath}")
        return False
    
    # Preserve shebang if present
    lines = content.split("\n")
    new_content = ""
    
    if lines and lines[0].startswith("#!"):
        new_content = lines[0] + "\n" + header
        if len(lines) > 1:
            new_content += "\n".join(lines[1:])
    else:
        new_content = header + content
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  ✓ Added header: {filepath}")
        return True
    except PermissionError as e:
        print(f"  Failed to write {filepath}: {e}")
        return False


def scan_and_add_headers(root_dir: Path) -> tuple[int, int]:
    """Scan directory and add headers to files."""
    added_count = 0
    total_checked = 0
    
    for filepath in root_dir.rglob("*"):
        if not filepath.is_file():
            continue
        
        if should_skip(filepath):
            continue
        
        # Check if file extension needs header
        header = HEADER_EXTENSIONS.get(filepath.suffix)
        if not header:
            continue
        
        total_checked += 1
        
        if add_header_to_file(filepath, header):
            added_count += 1
    
    return added_count, total_checked


def main():
    """Main function."""
    print("Scanning for files that need license headers...\n")
    
    root_dir = Path(__file__).parent.parent
    added, total = scan_and_add_headers(root_dir)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Files checked: {total}")
    print(f"  Headers added: {added}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
