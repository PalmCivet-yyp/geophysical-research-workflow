#!/usr/bin/env python3
"""生成包含完整台账的纯合成科研示例，展示证据登记与文件溯源。

该示例先登记实验，再生成示例数据，最后填写结果文件与哈希。
演示中的“已核验”仅指合成演示的文件结构已检查，绝非真实科研判断。
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
    """返回当前UTC时间，供示例说明登记与运行时间的先后关系。

    本示例中的系统时间可以被更改，不应被用作不可篡改的事前注册证据。
    """
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def add_csv(path,fields):
    """向模板CSV末尾追加一条记录，保留模板第一行预定义的字段名。"""
    with path.open("a",newline="",encoding="utf-8") as f:
        csv.writer(f).writerow(fields)


def build(destination):
    """在全新/空目录中构造带实验、结果、结论和哈希的示例研究项目。

    如目标目录非空则主动拒绝覆盖，保护潜在的实际科研文件。
    最后调用主验证器，确认合成示例可形成可追溯的结构闭环。
    """
    dest=destination.resolve()
    if dest.exists() and any(dest.iterdir()):
        raise ValueError("The output must be a new/empty directory; refusing to overwrite research files")
    # 通过主模块初始化与真实项目一致的空白台账（但目录必须在仓库外）。
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

    # 严格在生成合成数据前记录实验设计及“事先确定”的演示规则。
    # 这仅表明脚本执行顺序，不等价于真实科学研究中的正式预注册。
    registered_at=utc()
    add_csv(dest/"experiment_registry.csv",[
      "TOY-001","other","toy-generated-observation",registered_at,"","planned",
      "Illustrative 1D blur produces a traceable metrics file",
      "Required demo files exist and contain a fixed seed; no geological decision","seed=137; blur sigma=1 arbitrary unit","results/demo_metrics.json"])
    # 实际生成数据：使用固定种子的纯合成信号，与真实观测资料无关。
    demo_resolution.run(dest/"results")
    executed_at=utc()
    # 运行完毕后修改“同一条”实验登记，记录结果时间和流程核查状态。
    # 不能据此宣称经过独立、前瞻性的科研试验验证。
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
    # 将两个真实存在的输出文件分别写入SHA-256清单，供一致性核对。
    for filename in ["demo_metrics.json","synthetic_profiles.csv"]:
        f=dest/"results"/filename
        add_csv(dest/"file_manifest.csv",[
          "results/"+filename,workflow.sha256(f),"synthetic-only local generator", "original toy data"])
    # 做端到端结构核查；一旦失败则不将该示例报告为可复用成功案例。
    errs=workflow.validate(dest)
    for m in errs:print(m)
    if any(m.startswith("ERROR:") for m in errs):
        raise RuntimeError("Toy integration failed structural verification")
    print("TOY_PROJECT: STRUCTURE_OK_SCIENCE_UNVERIFIED (no physical inference)")
    return dest


# CLI参数为示例输出目录，例如：python scripts/build_toy_project.py ../toy-audited-project
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("destination",type=Path)
    args=p.parse_args()
    try:build(args.destination)
    except (OSError,ValueError,RuntimeError) as e:
        print(f"ERROR: {e}",file=sys.stderr)
        sys.exit(1)
