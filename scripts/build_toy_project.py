#!/usr/bin/env python3
"""Create a self-contained *synthetic-only* example with an honest dated toy registration.

This example checks file/provenance wiring, NOT scientific identifiability.
"""
import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import demo_resolution
import workflow


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def add_csv(path,fields):
    with path.open("a",newline="",encoding="utf-8") as f:
        csv.writer(f).writerow(fields)


def build(destination):
    dest=destination.resolve()
    if dest.exists() and any(dest.iterdir()):
        raise ValueError("The output must be a new/empty directory; refusing to overwrite research files")
    workflow.init(dest)
    config=json.loads((dest/"project.json").read_text())
    config.update({
      "project_id":"illustrative-1d-blur-only",
      "research_question":"Does this script reliably produce and track toy 1D blurred synthetic profiles?",
      "status":"active", "updated_utc":utc(),
      "spatial_context": {
        "crs":"not_applicable (abstract 1D coordinate)",
        "horizontal_domain":"-4 to +4 (abstract synthetic x coordinate)",
        "vertical_datum":"not_applicable",
        "depth_positive":"not_applicable",
        "units":"arbitrary signal units"
      },
      "datasets":[{
        "dataset_id":"toy-generated-observation","role":"observation",
        "name":"Gaussian-smoothed toy profiles (not measured)",
        "source":"scripts/demo_resolution.py deterministic generator",
        "version":"v1", "license_notes":"Synthetic-only original example; no third-party data"
      }]
    })
    (dest/"project.json").write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    registered_at=utc()
    add_csv(dest/"experiment_registry.csv",[
      "TOY-001","other","toy-generated-observation",registered_at,"","planned",
      "Illustrative 1D blur produces a traceable metrics file",
      "Required demo files exist and contain a fixed seed; no geological decision","seed=137; blur sigma=1 arbitrary unit","results/demo_metrics.json"])
    # The dated toy registration record is written BEFORE this local demo runs.
    demo_resolution.run(dest/"results")
    executed_at=utc()
    # Editing the *same* clearly toy experiment; this is not an assertion of prospective scientific validation.
    register=dest/"experiment_registry.csv"
    with register.open("r",newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f)); fields=list(rows[0])
    rows[0]["executed_at_utc"]=executed_at
    rows[0]["status"]="validated"
    with register.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    add_csv(dest/"evidence_ledger.csv",[
      "TOY-CLAIM-001", "This synthetic-only script records a blur sigma of 1 arbitrary unit", "TOY-001",
      "results/demo_metrics.json", "blur_sigma_arbitrary_units", "Fixed input parameter, not inferred",
      "Not a geophysical forward operator or evidence of real-world detection", "validated", "For the toy example only"])
    for filename in ["demo_metrics.json","synthetic_profiles.csv"]:
        f=dest/"results"/filename
        add_csv(dest/"file_manifest.csv",[
          "results/"+filename,workflow.sha256(f),"synthetic-only local generator", "original toy data"])
    errs=workflow.validate(dest)
    for m in errs:print(m)
    if any(m.startswith("ERROR:") for m in errs):
        raise RuntimeError("Toy integration failed structural verification")
    print("TOY_PROJECT: STRUCTURE_OK_SCIENCE_UNVERIFIED (no physical inference)")
    return dest


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination",type=Path)
    args=p.parse_args()
    try:build(args.destination)
    except (OSError,ValueError,RuntimeError) as e:
        print(f"ERROR: {e}",file=sys.stderr)
        sys.exit(1)
