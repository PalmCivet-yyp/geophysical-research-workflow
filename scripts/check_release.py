#!/usr/bin/env python3
"""公开发布前的启发式静态扫描（不是安全或版权认证）。

扫描源码结构、危险目录、文件大小、可疑密钥及个人联系信息。
无法扫描Git历史记录、二进制内部隐藏信息，也无法判定第三方版权归属。
每次发布仍需研究者人工确认合作方授权和未发表资料的保密义务。
"""
import re
import sys
from pathlib import Path

# 这些通常属于工具自动生成的环境/缓存目录，不作为公开源码扫描对象。
IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache"}
# 为防止真实研究项目误入公开仓库，列出需要排除的常见数据目录。
# 注意：目录名检查是保守策略，项目如需改变结构应同步更新测试。
FORBIDDEN_DIRS = {"venv", ".venv", "node_modules", "private", "raw", "data", "results", "figures", "notes", "outputs", "toy-output", "my-study"}
# 大部分科研原始数据、可执行密钥、地图及办公文件不应混入Skill源码发布包。
FORBIDDEN_SUFFIXES = {".pdf", ".doc", ".docx", ".zip", ".nc", ".npz", ".h5", ".hdf5", ".tif", ".tiff", ".grd", ".pem", ".p12", ".key", ".shp", ".dbf", ".shx"}
ALLOWED = {".md", ".py", ".txt", ".json", ".csv", ".yml", ".yaml", ".gitignore", "LICENSE", ".gitattributes"}
# 对常见密钥与个人联系信息使用正则启发式识别。
# 不完整的格式、变形编码和提交历史中的泄露，都可能无法被这里发现。
PATTERNS = {
    "GitHub access token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    "OpenAI-style key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Assigned credential": re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[=:]\s*['\"]?[A-Za-z0-9_\-./+]{20,}"),
    "Email address": re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I),
    "Chinese mobile number": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
}


def scan(root):
    """扫描一个候选公开仓库，返回 (错误列表, 警告列表, 文件数)。

    ERROR表示必须先处理的结构/文件风险；WARN表示需人工审查的事项。
    返回结果不包含“安全认证”含义，发布者仍要确认授权和资料归属。
    """
    errors=[]
    warnings=[]
    required=["SKILL.md", "README.md", "README.zh-CN.md", "LICENSE", ".gitignore", "scripts/workflow.py", "scripts/check_release.py", "scripts/validate_skill.py", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md", ".github/workflows/ci.yml"]
    # 必需文件缺失意味着别人无法安装/复现或无法找到安全说明。
    for fn in required:
        if not (root/fn).is_file():errors.append(f"Required file missing: {fn}")
    from validate_skill import validate as validate_frontmatter
    for issue in validate_frontmatter(root):
        errors.append(f"Skill metadata: {issue}")
    sk=root/"SKILL.md"
    if sk.is_file():
        content=sk.read_text(encoding="utf-8")
        sections=content.split("---", 2)
        if not content.startswith("---\n") or len(sections) < 3:
            errors.append("SKILL.md YAML frontmatter absent")
        else:
            front=sections[1]
            name=re.search(r"(?m)^name:\s*(\S+)\s*$",front)
            desc=re.search(r"(?m)^description:\s*(.*)$",front)
            if not name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",name.group(1)) or (name and name.group(1)!=root.name):
                errors.append("SKILL.md: invalid/mismatched name")
            if not desc or not 1<=len(desc.group(1).strip())<=1024:
                errors.append("SKILL.md: missing/oversize description")
    count=0
    forbidden_found = set()
    # 遍历目录：优先处理符号链接，避免通过链接指向仓库外的敏感文件。
    for p in root.rglob("*"):
        rel_parts = p.relative_to(root).parts
        if any(part in IGNORE_DIRS for part in rel_parts):continue
        bad_dirs = set(rel_parts[:-1] if p.is_file() else rel_parts) & FORBIDDEN_DIRS
        for name in bad_dirs:
            if name not in forbidden_found:
                errors.append(f"Forbidden research/dependency directory in publication source: {name}/")
                forbidden_found.add(name)
        if p.is_symlink():
            errors.append(f"Symlink requires review: {p.relative_to(root)}")
            continue
        if not p.is_file(): continue
        count+=1
        rel=str(p.relative_to(root))
        if p.name.startswith(".env") or p.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Potential non-public file: {rel}")
        if p.stat().st_size>2*1024*1024:
            errors.append(f"Large file (manual license/secret audit): {rel}")
        if p.suffix.lower() not in ALLOWED and p.name not in ALLOWED and not p.name.startswith("."):
            warnings.append(f"Nonstandard extension, review: {rel}")
        # 仅对体积较小的文本文件尝试UTF-8读取与可疑字段扫描。
        # 超过阈值的文件应交由人工专门检查；并非意味着大文件就是安全的。
        if p.stat().st_size<2*1024*1024:
            try:txt=p.read_text(encoding="utf-8")
            except UnicodeDecodeError:errors.append(f"Binary data detected: {rel}");continue
            for label,pat in PATTERNS.items():
                if pat.search(txt): errors.append(f"{label} candidate in: {rel}")
    return errors, warnings, count


def main():
    """命令行预发布核查：发现ERROR则返回非零退出码供CI拦截。"""
    root=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
    errors,warnings,n=scan(root)
    for s in errors:print("ERROR:",s)
    for s in warnings:print("WARN:",s)
    print(f"RELEASE_PREFLIGHT: {'FAIL' if errors else 'STATIC_CHECK_PASS_MANUAL_REVIEW_REQUIRED'} files={n}, errors={len(errors)}, warnings={len(warnings)}")
    # 即使没有发现错误，仍向发布者强调人工审核属于不可省略的步骤。
    print("Still required: contributor permission, third-party license review, manual identifier/secret audit, and an independent Git history scan.")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
