#!/usr/bin/env python3
"""Offline frontmatter sanity check for this repository's simple YAML fields.

Not a full YAML parser: run the official `skills-ref validate` when available.
"""
import re
import sys
from pathlib import Path

VALID_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

def validate(root: Path):
    errors = []
    path = root / "SKILL.md"
    if not path.is_file():
        return ["SKILL.md not found"]
    content = path.read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    if len(lines) < 5 or lines[0] != "---":
        return ["SKILL.md must start with --- YAML frontmatter"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return ["SKILL.md frontmatter has no closing ---"]
    if not any(line.strip().startswith("# ") for line in lines[end+1:]):
        errors.append("SKILL.md body needs an H1 heading")
    values = {}
    metadata = {}
    in_metadata = False
    for i, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  ") and in_metadata:
            match = re.fullmatch(r"  ([\w-]+):\s*(.+?)\s*", line)
            if not match:
                errors.append(f"line {i}: invalid metadata field")
            else:
                metadata[match[1]] = match[2].strip("\"'")
            continue
        in_metadata = False
        match = re.fullmatch(r"([\w-]+):\s*(.*?)\s*", line)
        if not match:
            errors.append(f"line {i}: unexpected/unsupported YAML form; use a simple scalar")
            continue
        key, val = match.groups()
        if key in values:
            errors.append(f"line {i}: duplicate frontmatter key {key}")
        if key not in VALID_KEYS:
            errors.append(f"line {i}: unsupported key {key}")
        values[key] = val.strip("\"'")
        in_metadata = key == "metadata" and not val
    name = values.get("name", "")
    description = values.get("description", "")
    if not NAME_PATTERN.fullmatch(name) or len(name) > 64 or name != root.name:
        errors.append("invalid name or directory name mismatch")
    if not 1 <= len(description) <= 1024:
        errors.append("description must be 1..1024 characters")
    if len(values.get("compatibility", "")) > 500:
        errors.append("compatibility must be at most 500 characters")
    if "metadata" in values and not metadata:
        errors.append("metadata mapping must be nonempty")
    if not metadata.get("version"):
        errors.append("metadata.version is required by this repository")
    if len(lines) > 500:
        errors.append("SKILL.md exceeds 500 lines")
    return errors

if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    for err in errors:
        print(f"ERROR: {err}")
    print("SKILL_FRONTMATTER:", "BASIC_PASS_CHECK_WITH_OFFICIAL_SKILLS_REF" if not errors else "FAIL")
    raise SystemExit(1 if errors else 0)
