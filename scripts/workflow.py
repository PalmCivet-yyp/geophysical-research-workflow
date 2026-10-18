#!/usr/bin/env python3
"""科研台账的离线结构核查工具（非地球物理求解器）。

功能范围：初始化独立科研目录、检查元数据与证据文件之间的关系、计算文件哈希。
重要限制：通过检查仅表明台账在预设规则下结构一致，不证明反演或地质解释正确。
所有科研数据默认存放在仓库之外，避免误将未公开资料提交到 GitHub。
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

# 这里的 ROOT 指 Skill 的“源码目录”，不是研究项目目录。
# 研究项目应通过命令行单独指定，二者不能混用。
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
# 五类台账的必填列名。格式和列名作为后续跨表校验的共同契约。
# 修改字段时，必须同步更新 assets 模板、references 说明以及单元测试。
TABLES = {
    "experiment_registry.csv": "experiment_id,analysis_type,dataset_ids,registered_at_utc,executed_at_utc,status,hypothesis,decision_rule,controls,output_path",
    "evidence_ledger.csv": "claim_id,claim_text,experiment_id,result_path,locator,uncertainty,limitations,status,allowed_wording",
    "figure_manifest.csv": "figure_id,figure_path,source_data_path,code_path,units,crs,display_transforms,status",
    "citation_audit.csv": "citation_id,claim_ids,doi_or_url,title,authors,year,metadata_verified,direct_support_verified,notes",
    "file_manifest.csv": "relative_path,sha256,origin,license_notes",
}
# 数据角色是科研证据独立性判断的核心：
# observation=观测；geometry=几何条件；prior=反演前置先验；
# external_model=外部对比模型；posthoc_diagnostic=结果形成后的诊断；context=背景材料。
ROLES = {"observation", "geometry", "prior", "external_model", "posthoc_diagnostic", "context"}
VALID_EXP = {"planned", "running", "validated", "failed", "superseded"}
VALID_CLAIM = {"draft", "validated", "rejected", "superseded"}
VALID_ANALYSIS = {"gravity_only", "prior_conditioned", "posthoc_diagnostic", "other"}
# 时间戳统一要求 UTC，避免不同时区造成“先登记还是先运行”的混淆。
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)$")


def is_utc(value):
    """检查时间字符串是否符合 UTC ISO-8601 格式且日期本身合法。

    这里只检查文本格式与历法有效性；无法证实记录确实在该时刻创建。
    若要证明事前登记，需要不可篡改日志或带时间的版本提交作为辅助证据。
    """
    if not TIMESTAMP_RE.fullmatch(value or ""):
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def safe_path(root, rel, messages, label, must_exist=False):
    """解析项目内相对路径，拒绝绝对路径、上级跳转及符号链接越界。

    参数：root 为研究项目根目录；rel 为待登记的相对路径；messages 收集错误；
    label 用于定位报错字段；must_exist 控制是否要求该路径对应现有文件。
    返回：安全解析的 Path；字段缺失或越界时返回 None。
    """
    if not rel:
        messages.append(f"ERROR: {label}: path missing")
        return None
    if not isinstance(rel, str):
        messages.append(f"ERROR: {label}: path is not text")
        return None
    # 第一道防护：直接拒绝绝对路径与 `..` 路径穿越。
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        messages.append(f"ERROR: {label}: unsafe path {rel!r}")
        return None
    # 第二道防护：resolve() 会解析符号链接，避免链接到项目外的私有数据。
    resolved = (root / p).resolve()
    if not resolved.is_relative_to(root.resolve()):
        messages.append(f"ERROR: {label}: path escapes project {rel!r}")
        return None
    if must_exist and not resolved.is_file():
        messages.append(f"ERROR: {label}: file does not exist: {rel!r}")
    return resolved


def read_rows(root, filename, messages):
    """读取一个 CSV 台账，并按预定义字段集合验证基本格式。

    对缺少表头、缺列、数据行列数不一致或 CSV 转义异常返回错误信息。
    utf-8-sig 兼容部分 Windows/Excel 导出时附带的 UTF-8 BOM。
    这里只检查“文本结构”，并不推断字段内容在科学意义上是否正确。
    """
    path = root / filename
    if not path.is_file():
        messages.append(f"ERROR: missing {filename}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        # 使用包含关系而不是要求列顺序完全相同：允许增加自定义列。
        required = set(TABLES[filename].split(","))
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            messages.append(f"ERROR: {filename}: missing columns: {sorted(required-set(reader.fieldnames or []))}")
            return []
        try:
            rows = list(reader)
        except csv.Error as exc:
            messages.append(f"ERROR: {filename}: invalid CSV ({exc})")
            return []
        # DictReader 在超出表头长度时会生成键 None，表示这一行有多余列。
        if any(None in r for r in rows):
            messages.append(f"ERROR: {filename}: excessive unnamed columns")
        if any(any(value is None for value in row.values()) for row in rows):
            messages.append(f"ERROR: {filename}: rows with missing columns")
        return [{key: (value if isinstance(value, str) else "") for key, value in row.items() if key is not None} for row in rows]


def check_unique(rows, key, filename, messages):
    """检查台账的主键是否填写及重复，错误行号从 CSV 第2行开始。

    每项实验、论文结论、图件和引文都应拥有稳定的唯一标识，
    否则后续的“结论→试验→输出”关系可能关联错对象。
    """
    seen = set()
    for i, r in enumerate(rows, 2):
        v = (r.get(key) or "").strip()
        if not v:
            messages.append(f"ERROR: {filename}:{i}: missing {key}")
        elif v in seen:
            messages.append(f"ERROR: {filename}:{i}: duplicate {key}={v}")
        seen.add(v)


def validate(root):
    """综合核查科研项目中的 JSON/CSV 登记关系，返回错误与提醒列表。

    核查顺序：项目基础信息 → 数据角色 → 台账主键 → 试验登记 →
    定量结论 → 图件与引文 → 文件路径及 SHA-256 → 缺失证据提醒。
    每条消息以 ERROR 或 WARN 开头；调用方负责决定退出码。

    重要：此处的 validated 仅表示研究者在台账里填写的状态，
    不应被解释为论文结论通过学术审查、真实反演结果得到确认。
    """
    msgs = []
    if not root.is_dir():
        return [f"ERROR: not a directory: {root}"]
    # 第一步：读取项目元信息。文件不存在/JSON损坏时直接终止后续核查。
    proj_path = root / "project.json"
    try:
        project = json.loads(proj_path.read_text(encoding="utf-8"))
        if not isinstance(project, dict):
            raise ValueError("project must be an object")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        return [f"ERROR: cannot load project.json: {e}"]
    for k in ["project_id", "research_question", "status", "updated_utc"]:
        if not isinstance(project.get(k), str) or not project[k].strip() or project[k] == "replace-me":
            msgs.append(f"ERROR: project.json: fill {k}")
    if project.get("status") not in {"draft", "active", "completed", "archived"}:
        msgs.append("ERROR: project.json: invalid status")
    if not is_utc(project.get("updated_utc", "")):
        msgs.append("ERROR: project.json: updated_utc must be UTC ISO8601 (e.g. 2026-01-01T12:00:00Z)")
    # 坐标参考、深度正方向和单位不明确时，跨数据比较容易出错。
    # 当前只检查是否填写，并不会计算坐标转换或量纲一致性。
    spatial = project.get("spatial_context")
    if not isinstance(spatial, dict):
        msgs.append("ERROR: project.json: spatial_context must be an object")
    else:
        for k in ["crs", "horizontal_domain", "vertical_datum", "depth_positive", "units"]:
            if not isinstance(spatial.get(k), str) or not spatial[k].strip():
                msgs.append(f"ERROR: project.json: spatial_context.{k} missing")
    # 第二步：记录输入数据的来源、版本、许可和角色；禁止同名 dataset_id。
    # “仅基于重力资料”的说法可能还依赖模型几何，所以需要精确登记角色。
    datasets = project.get("datasets", [])
    if not isinstance(datasets, list):
        msgs.append("ERROR: project.json: datasets must be an array")
        datasets = []
    dmap = {}
    for i, d in enumerate(datasets):
        if not isinstance(d, dict):
            msgs.append(f"ERROR: dataset[{i}] is not an object")
            continue
        for k in ["dataset_id", "role", "name", "source", "version", "license_notes"]:
            if not isinstance(d.get(k), str) or not d[k].strip():
                msgs.append(f"ERROR: dataset[{i}] missing {k}")
        ident = d.get("dataset_id", "")
        if not isinstance(ident, str):
            ident = ""
        if ident in dmap:
            msgs.append(f"ERROR: duplicate dataset_id {ident}")
        if d.get("role") not in ROLES:
            msgs.append(f"ERROR: dataset[{i}] invalid role {d.get('role')}")
        if ident:
            dmap[ident] = d
    # 第三步：载入五份 CSV。它们共同构成跨文件的证据链。
    exp = read_rows(root, "experiment_registry.csv", msgs)
    claims = read_rows(root, "evidence_ledger.csv", msgs)
    figures = read_rows(root, "figure_manifest.csv", msgs)
    citations = read_rows(root, "citation_audit.csv", msgs)
    files = read_rows(root, "file_manifest.csv", msgs)
    for rows, filename, key in [
        (exp,"experiment_registry.csv","experiment_id"),
        (claims,"evidence_ledger.csv","claim_id"),
        (figures,"figure_manifest.csv","figure_id"),
        (citations,"citation_audit.csv","citation_id"),
        (files,"file_manifest.csv","relative_path"),
    ]:
        check_unique(rows,key,filename,msgs)
    # 建立 ID→记录索引，以便逐条查找结论依赖的具体实验。
    exmap = {r["experiment_id"]:r for r in exp if r.get("experiment_id")}
    clmap = {r["claim_id"]:r for r in claims if r.get("claim_id")}
    # validated 是研究者登记的工作流状态，不是本程序授予的科学认证。
    # 以下检查只要求相关文件、校验值和时间记录在结构上成立。
    manifest_map = {r.get("relative_path", ""): r for r in files}
    # 第四步：逐项检查实验登记，重点防止错误标记独立反演证据。
    for i, r in enumerate(exp, 2):
        label = f"experiment_registry.csv:{i}"
        status,kind = r.get("status",""),r.get("analysis_type","")
        if status not in VALID_EXP: msgs.append(f"ERROR: {label}: invalid status={status}")
        if kind not in VALID_ANALYSIS: msgs.append(f"ERROR: {label}: invalid analysis_type={kind}")
        # dataset_ids 用“|”分隔；每个 ID 都必须在 project.json 中定义。
        ids = [x.strip() for x in r.get("dataset_ids", "").split("|") if x.strip()]
        if status in {"running", "validated"} and not ids:
            msgs.append(f"ERROR: {label}: active experiment has no input datasets")
        for ident in ids:
            if ident not in dmap:
                msgs.append(f"ERROR: {label}: unknown dataset {ident}")
            # gravity_only 不应将三维密度先验、外部模型或后验诊断当作观测输入。
            # geometry 可作为已声明的几何条件，但不得因此宣称整个反演无任何先验。
            elif kind == "gravity_only" and dmap[ident].get("role") in {"prior", "external_model", "posthoc_diagnostic"}:
                msgs.append(f"ERROR: {label}: gravity_only uses a prior/external/posthoc input: {ident}")
        reg = r.get("registered_at_utc", "")
        exe = r.get("executed_at_utc", "")
        if status in {"running", "validated"} and not is_utc(reg):
            msgs.append(f"ERROR: {label}: invalid preregistration timestamp")
        if exe and not is_utc(exe):
            msgs.append(f"ERROR: {label}: invalid execution timestamp")
        # 若登记时间晚于执行时间，提示“事后登记”，不把此项冒充事前试验设计。
        if is_utc(reg) and is_utc(exe) and dt.datetime.fromisoformat(reg.replace("Z", "+00:00")) > dt.datetime.fromisoformat(exe.replace("Z", "+00:00")):
            msgs.append(f"ERROR: {label}: preregistration timestamp is after execution")
        # 仅在研究者声明“已核验”时加强要求：必须有控制条件、判定规则、
        # 实际结果文件以及文件哈希登记；哈希匹配仍不证明结果物理有效。
        if status == "validated":
            if not exe or not r.get("decision_rule") or not r.get("controls"):
                msgs.append(f"ERROR: {label}: validated experiment missing date/gate/controls")
            output_rel = r.get("output_path", "")
            safe_path(root, output_rel, msgs, label+" output", must_exist=True)
            entry = manifest_map.get(output_rel)
            if not entry or not entry.get("sha256"):
                msgs.append(f"ERROR: {label}: validated output requires SHA256 entry in file_manifest.csv")
    # 第五步：检查论文每条“已核验结论”是否能回溯到实验和结果文件。
    # 同时要求记录不确定性、限制及结果文件内的具体定位字段。
    for i, r in enumerate(claims, 2):
        label = f"evidence_ledger.csv:{i}"
        status = r.get("status", "")
        if status not in VALID_CLAIM: msgs.append(f"ERROR: {label}: invalid status={status}")
        if status == "validated":
            if not r.get("claim_text") or not r.get("locator") or not r.get("uncertainty") or not r.get("limitations"):
                msgs.append(f"ERROR: {label}: validated claim missing text/locator/uncertainty/limitations")
            target = exmap.get(r.get("experiment_id",""))
            if not target or target.get("status") != "validated":
                msgs.append(f"ERROR: {label}: validated claim lacks validated experiment")
            result_rel = r.get("result_path", "")
            safe_path(root, result_rel, msgs, label+" result", must_exist=True)
            if result_rel != (target or {}).get("output_path") and result_rel not in manifest_map:
                msgs.append(f"ERROR: {label}: claim result is not experiment output or registered in file_manifest.csv")
            entry = manifest_map.get(result_rel)
            if not entry or not entry.get("sha256"):
                msgs.append(f"ERROR: {label}: validated claim requires SHA256 entry in file_manifest.csv")
    # 第六步：正式图件至少需登记源数据、绘图代码、单位、CRS与显示变换。
    # 不能把通过插值/平滑的显示图误写成原始分辨率的观测结果。
    for i, r in enumerate(figures, 2):
        label = f"figure_manifest.csv:{i}"
        if r.get("status") not in {"draft", "final", "retired"}:
            msgs.append(f"ERROR: {label}: invalid figure status")
        if r.get("status") == "final":
            for k in ["figure_path","source_data_path","code_path"]:
                safe_path(root,r.get(k,""),msgs,label+" "+k,must_exist=True)
            for k in ["units","crs","display_transforms"]:
                if not r.get(k): msgs.append(f"ERROR: {label}: missing {k}")
    # 第七步：引文元信息与“是否直接支持此论断”是两个不同检查项。
    # 不允许在文献信息尚未核对的情况下标记其直接支持某项结论。
    for i, r in enumerate(citations, 2):
        label = f"citation_audit.csv:{i}"
        for k in ["metadata_verified","direct_support_verified"]:
            if r.get(k) not in {"yes", "no", "pending"}:
                msgs.append(f"ERROR: {label}: invalid {k}")
        if r.get("direct_support_verified") == "yes" and r.get("metadata_verified") != "yes":
            msgs.append(f"ERROR: {label}: direct support cannot be verified when metadata is not")
        for clid in [x.strip() for x in r.get("claim_ids", "").split("|") if x.strip()]:
            if clid not in clmap:
                msgs.append(f"ERROR: {label}: unknown claim_id {clid}")
    # 第八步：核对文件清单的路径限制、哈希格式、当前文件内容和版权信息。
    # SHA-256能够检测“登记时与现在不一致”，但不能证明科研数据来源真实。
    for i, r in enumerate(files, 2):
        label = f"file_manifest.csv:{i}"
        path = safe_path(root,r.get("relative_path",""),msgs,label,must_exist=True)
        digest = r.get("sha256", "")
        if digest:
            if not re.fullmatch(r"[a-fA-F0-9]{64}",digest):
                msgs.append(f"ERROR: {label}: invalid SHA256 syntax")
            elif path and path.is_file() and sha256(path) != digest.lower():
                msgs.append(f"ERROR: {label}: SHA256 mismatch")
        if not r.get("origin") or not r.get("license_notes"):
            msgs.append(f"ERROR: {label}: missing origin / license notes")
    # 警告与错误分开：没有证据可核验时必须明确提示，而非装作验证成功。
    if not exp:
        msgs.append("WARN: no registered experiments; no scientific results verified")
    if not claims:
        msgs.append("WARN: empty evidence ledger; no claims verified")
    if not citations:
        msgs.append("WARN: empty citation audit; literature support unverified")
    return msgs


def sha256(path):
    """以分块方式计算文件的 SHA-256 校验值，避免一次将大文件加载到内存。

    返回64位十六进制字符串，供 file_manifest.csv 记录。
    同一个哈希并不提供学术意义上的真实性、授权或因果证明。
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def init(root):
    """在独立目录创建空白科研项目，不覆盖已经存在的台账和文件。

    安全要求：拒绝在Skill源码根目录及其子目录初始化研究项目，
    避免真实数据、论文和审稿文件被下一次 git add 意外包含。
    """
    root = root.resolve()
    # Keep research datasets/registries out of the public source checkout by default.
    if root == ROOT or ROOT in root.parents:
        raise ValueError("Refusing to create a research project inside the public skill checkout; use an external directory (e.g. ../research-study).")
    root.mkdir(parents=True, exist_ok=True)
    # 从随仓库发布的空白模板复制 JSON/CSV；已存在文件一律保留。
    for name in ["project.json",*TABLES]:
        dst = root / name
        if dst.exists():
            print(f"PRESERVED: {dst}")
        else:
            shutil.copyfile(ASSETS / name, dst)
            print(f"CREATED: {dst}")
    for d in ["data", "results", "figures", "code", "notes"]:
        (root / d).mkdir(exist_ok=True)
    print("INCOMPLETE: edit project.json, register inputs, and run validate. This is not a validated study.")


def main():
    """命令行入口：init 初始化、validate 验证、hash 输出文件哈希。

    validate 如有结构错误返回1；初始化或文件读取等用法错误返回2；
    结构核验成功返回0，并明确输出 SCIENCE_UNVERIFIED，防止误读。
    """
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd",required=True)
    for cmd in ["init","validate"]:
        x=sub.add_parser(cmd)
        x.add_argument("project", type=Path)
    y=sub.add_parser("hash")
    y.add_argument("files",type=Path,nargs="+")
    args=p.parse_args()
    if args.cmd == "init":
        try:
            init(args.project.resolve())
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        return 0
    if args.cmd == "hash":
        for f in args.files:
            if not f.is_file():
                print(f"ERROR: missing {f}",file=sys.stderr);return 2
            print(sha256(f), f)
        return 0
    # 命令退出码可供CI使用，但不代表科学研究通过同行评审或独立复核。
    errors=validate(args.project.resolve())
    for m in errors: print(m)
    bad=sum(m.startswith("ERROR:") for m in errors)
    print(f"VALIDATION: {'FAIL' if bad else 'STRUCTURE_OK_SCIENCE_UNVERIFIED'} (errors={bad}, warnings={len(errors)-bad})")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
