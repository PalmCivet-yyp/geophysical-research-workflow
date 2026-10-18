#!/usr/bin/env python3
"""Offline metadata/evidence linkage checks; not a geophysical solver or scientific proof."""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TABLES = {
    "experiment_registry.csv": "experiment_id,analysis_type,dataset_ids,registered_at_utc,executed_at_utc,status,hypothesis,decision_rule,controls,output_path",
    "evidence_ledger.csv": "claim_id,claim_text,experiment_id,result_path,locator,uncertainty,limitations,status,allowed_wording",
    "figure_manifest.csv": "figure_id,figure_path,source_data_path,code_path,units,crs,display_transforms,status",
    "citation_audit.csv": "citation_id,claim_ids,doi_or_url,title,authors,year,metadata_verified,direct_support_verified,notes",
    "file_manifest.csv": "relative_path,sha256,origin,license_notes",
}
ROLES = {"observation", "geometry", "prior", "external_model", "posthoc_diagnostic", "context"}
VALID_EXP = {"planned", "running", "validated", "failed", "superseded"}
VALID_CLAIM = {"draft", "validated", "rejected", "superseded"}
VALID_ANALYSIS = {"gravity_only", "prior_conditioned", "posthoc_diagnostic", "other"}
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)$")


def is_utc(value):
    if not TIMESTAMP_RE.fullmatch(value or ""):
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def safe_path(root, rel, messages, label, must_exist=False):
    """Return confined file path; reject absolute paths and traversals."""
    if not rel:
        messages.append(f"ERROR: {label}: path missing")
        return None
    if not isinstance(rel, str):
        messages.append(f"ERROR: {label}: path is not text")
        return None
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        messages.append(f"ERROR: {label}: unsafe path {rel!r}")
        return None
    resolved = (root / p).resolve()
    if not resolved.is_relative_to(root.resolve()):
        messages.append(f"ERROR: {label}: path escapes project {rel!r}")
        return None
    if must_exist and not resolved.is_file():
        messages.append(f"ERROR: {label}: file does not exist: {rel!r}")
    return resolved


def read_rows(root, filename, messages):
    path = root / filename
    if not path.is_file():
        messages.append(f"ERROR: missing {filename}")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        required = set(TABLES[filename].split(","))
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            messages.append(f"ERROR: {filename}: missing columns: {sorted(required-set(reader.fieldnames or []))}")
            return []
        try:
            rows = list(reader)
        except csv.Error as exc:
            messages.append(f"ERROR: {filename}: invalid CSV ({exc})")
            return []
        if any(None in r for r in rows):
            messages.append(f"ERROR: {filename}: excessive unnamed columns")
        if any(any(value is None for value in row.values()) for row in rows):
            messages.append(f"ERROR: {filename}: rows with missing columns")
        return [{key: (value if isinstance(value, str) else "") for key, value in row.items() if key is not None} for row in rows]


def check_unique(rows, key, filename, messages):
    seen = set()
    for i, r in enumerate(rows, 2):
        v = (r.get(key) or "").strip()
        if not v:
            messages.append(f"ERROR: {filename}:{i}: missing {key}")
        elif v in seen:
            messages.append(f"ERROR: {filename}:{i}: duplicate {key}={v}")
        seen.add(v)


def validate(root):
    msgs = []
    if not root.is_dir():
        return [f"ERROR: not a directory: {root}"]
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
    spatial = project.get("spatial_context")
    if not isinstance(spatial, dict):
        msgs.append("ERROR: project.json: spatial_context must be an object")
    else:
        for k in ["crs", "horizontal_domain", "vertical_datum", "depth_positive", "units"]:
            if not isinstance(spatial.get(k), str) or not spatial[k].strip():
                msgs.append(f"ERROR: project.json: spatial_context.{k} missing")
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
    exmap = {r["experiment_id"]:r for r in exp if r.get("experiment_id")}
    clmap = {r["claim_id"]:r for r in claims if r.get("claim_id")}
    # A recorded "validated" status is an author-supplied label, never a scientific certification.
    manifest_map = {r.get("relative_path", ""): r for r in files}
    for i, r in enumerate(exp, 2):
        label = f"experiment_registry.csv:{i}"
        status,kind = r.get("status",""),r.get("analysis_type","")
        if status not in VALID_EXP: msgs.append(f"ERROR: {label}: invalid status={status}")
        if kind not in VALID_ANALYSIS: msgs.append(f"ERROR: {label}: invalid analysis_type={kind}")
        ids = [x.strip() for x in r.get("dataset_ids", "").split("|") if x.strip()]
        if status in {"running", "validated"} and not ids:
            msgs.append(f"ERROR: {label}: active experiment has no input datasets")
        for ident in ids:
            if ident not in dmap:
                msgs.append(f"ERROR: {label}: unknown dataset {ident}")
            elif kind == "gravity_only" and dmap[ident].get("role") in {"prior", "external_model", "posthoc_diagnostic"}:
                msgs.append(f"ERROR: {label}: gravity_only uses a prior/external/posthoc input: {ident}")
        reg = r.get("registered_at_utc", "")
        exe = r.get("executed_at_utc", "")
        if status in {"running", "validated"} and not is_utc(reg):
            msgs.append(f"ERROR: {label}: invalid preregistration timestamp")
        if exe and not is_utc(exe):
            msgs.append(f"ERROR: {label}: invalid execution timestamp")
        if is_utc(reg) and is_utc(exe) and dt.datetime.fromisoformat(reg.replace("Z", "+00:00")) > dt.datetime.fromisoformat(exe.replace("Z", "+00:00")):
            msgs.append(f"ERROR: {label}: preregistration timestamp is after execution")
        if status == "validated":
            if not exe or not r.get("decision_rule") or not r.get("controls"):
                msgs.append(f"ERROR: {label}: validated experiment missing date/gate/controls")
            output_rel = r.get("output_path", "")
            safe_path(root, output_rel, msgs, label+" output", must_exist=True)
            entry = manifest_map.get(output_rel)
            if not entry or not entry.get("sha256"):
                msgs.append(f"ERROR: {label}: validated output requires SHA256 entry in file_manifest.csv")
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
    for i, r in enumerate(figures, 2):
        label = f"figure_manifest.csv:{i}"
        if r.get("status") not in {"draft", "final", "retired"}:
            msgs.append(f"ERROR: {label}: invalid figure status")
        if r.get("status") == "final":
            for k in ["figure_path","source_data_path","code_path"]:
                safe_path(root,r.get(k,""),msgs,label+" "+k,must_exist=True)
            for k in ["units","crs","display_transforms"]:
                if not r.get(k): msgs.append(f"ERROR: {label}: missing {k}")
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
    if not exp:
        msgs.append("WARN: no registered experiments; no scientific results verified")
    if not claims:
        msgs.append("WARN: empty evidence ledger; no claims verified")
    if not citations:
        msgs.append("WARN: empty citation audit; literature support unverified")
    return msgs


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def init(root):
    root = root.resolve()
    # Keep research datasets/registries out of the public source checkout by default.
    if root == ROOT or ROOT in root.parents:
        raise ValueError("Refusing to create a research project inside the public skill checkout; use an external directory (e.g. ../research-study).")
    root.mkdir(parents=True, exist_ok=True)
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
    errors=validate(args.project.resolve())
    for m in errors: print(m)
    bad=sum(m.startswith("ERROR:") for m in errors)
    print(f"VALIDATION: {'FAIL' if bad else 'STRUCTURE_OK_SCIENCE_UNVERIFIED'} (errors={bad}, warnings={len(errors)-bad})")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
