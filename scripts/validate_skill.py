#!/usr/bin/env python3
"""检查 SKILL.md 的基本前置信息（frontmatter）。

本程序只支持项目中使用的简明 YAML 标量/metadata 写法，不是完整 YAML 解析器。
因此通过本地检查后，仍建议在实际 Agent 环境或官方验证器中检查兼容性。
"""
import re
import sys
from pathlib import Path

# 允许的 frontmatter 顶级字段；防止写错字段名后被某些客户端忽略。
VALID_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

def validate(root: Path):
    """返回 Skill 元数据中的结构问题，不负责解释业务任务或验证科学结论。

    核查内容包括文件存在、YAML分隔符、合法名称、描述长度、版本等。
    name 应与目录名称保持一致，避免多个Skill被误识别为同一项。
    """
    errors = []
    path = root / "SKILL.md"
    if not path.is_file():
        return ["SKILL.md not found"]
    content = path.read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    if len(lines) < 5 or lines[0] != "---":
        return ["SKILL.md must start with --- YAML frontmatter"]
    # 只将第一对 `---` 之间的内容解释为元数据，正文不按 YAML 检查。
    try:
        end = lines.index("---", 1)
    except ValueError:
        return ["SKILL.md frontmatter has no closing ---"]
    if not any(line.strip().startswith("# ") for line in lines[end+1:]):
        errors.append("SKILL.md body needs an H1 heading")
    values = {}
    metadata = {}
    in_metadata = False
    # 当前实现仅解析单层键值对和metadata下方缩进两个空格的简单键值。
    # 不支持复杂列表、锚点、多行字符串等完整YAML特性。
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
    # 统一小写连字符命名，并约束文件夹名称与Agent调用名一致。
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

# CLI使用：python scripts/validate_skill.py .
# 非零退出码适合用于GitHub Actions阻止格式错误合入。
if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    for err in errors:
        print(f"ERROR: {err}")
    print("SKILL_FRONTMATTER:", "BASIC_PASS_CHECK_WITH_OFFICIAL_SKILLS_REF" if not errors else "FAIL")
    raise SystemExit(1 if errors else 0)
