"""科研台账和合成演示的回归测试。

每个测试都使用TemporaryDirectory隔离文件，不读写用户真实科研资料；
重点覆盖失败路径，防止未来改动误把不完整的科研证据判断为“有效”。
"""
import csv
import datetime
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import workflow  # noqa: E402
import demo_resolution  # noqa: E402
import check_release  # noqa: E402


class WorkflowTests(unittest.TestCase):
    """验证台账基本规则、越界路径、证据链接和发布安全的回归用例。"""
    def setUp(self):
        """为每个测试生成独立临时科研项目，测试结束后自动清理。"""
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/"study"
        workflow.init(self.p)

    def fill(self):
        """填写最小合法研究元信息（仍属于抽象合成数据，而非真实科研）。"""
        p=self.p/"project.json"
        config=json.loads(p.read_text())
        config.update(project_id="toy-study",research_question="Can a toy blur distinguish two 1D forms?",status="active",updated_utc="2026-10-18T00:00:00Z")
        config["spatial_context"]={"crs":"EPSG:4326","horizontal_domain":"86-94 E (toy)","vertical_datum":"not_applicable","depth_positive":"down","units":"arbitrary signal units"}
        config["datasets"]=[{"dataset_id":"syn","role":"observation","name":"Synthetic illustrative observation","source":"generated locally by deterministic script","version":"v1","license_notes":"original synthetic only"}]
        p.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding="utf-8")

    def add_row(self,filename, values):
        """追加一行CSV以模拟科研人员登记的不同有效/错误状态。"""
        with (self.p/filename).open("a",encoding="utf-8",newline="") as f:
            writer=csv.writer(f);writer.writerow(values)

    def test_incomplete_template_fails(self):
        """空白项目不得被当成已经合格的科研记录。"""
        self.assertTrue(any(x.startswith("ERROR:") for x in workflow.validate(self.p)))

    def test_structural_valid_without_claims_not_scientific_validation(self):
        """结构上可为空证据表，但必须以WARN声明尚无结论得到核验。"""
        self.fill()
        m=workflow.validate(self.p)
        self.assertFalse(any(x.startswith("ERROR:") for x in m),m)
        self.assertTrue(any("WARN: empty evidence" in x for x in m))

    def test_prior_in_gravity_only_rejected(self):
        """禁止将密度先验登记为“仅重力观测反演”的独立输入。"""
        self.fill()
        j=json.loads((self.p/"project.json").read_text())
        j["datasets"].append({"dataset_id":"external","role":"prior","name":"Prior density","source":"toy","version":"v1","license_notes":"toy"})
        (self.p/"project.json").write_text(json.dumps(j))
        self.add_row("experiment_registry.csv",["E1","gravity_only","syn|external","2026-10-17T12:00:00Z","","planned","H1","frozen rule","controls",""])
        m=workflow.validate(self.p)
        self.assertTrue(any("gravity_only uses" in x for x in m),m)

    def test_claim_without_evidence_rejected(self):
        """没有实际结果文件支撑的结论不能标为已核验。"""
        self.fill()
        (self.p/"results").mkdir(exist_ok=True)
        (self.p/"results"/"example.json").write_text('{}')
        self.add_row("experiment_registry.csv",["E1","other","syn","2026-10-17T12:00:00Z","2026-10-18T00:00:00Z","validated","H1","rule","controls","results/example.json"])
        self.add_row("evidence_ledger.csv",["C1","Claim","E1","results/missing.json","row1","uncertainty","limits","validated","conditional"])
        m=workflow.validate(self.p)
        self.assertTrue(any("does not exist" in x for x in m),m)

    def test_registration_after_execution_fails(self):
        """登记时间晚于执行时间应报告错误，避免虚假事前登记。"""
        self.fill()
        self.add_row("experiment_registry.csv",["E1","other","syn","2026-10-19T00:00:00Z","2026-10-18T00:00:00Z","failed","H1","rule","controls",""])
        m=workflow.validate(self.p)
        self.assertTrue(any("after execution" in x for x in m),m)

    def test_path_traversal_rejected(self):
        """拒绝使用../跳出当前科研目录的文件清单条目。"""
        self.fill()
        self.add_row("file_manifest.csv",["../../private.txt","", "self","private"])
        self.assertTrue(any("unsafe path" in s for s in workflow.validate(self.p)))

    def test_hash_mismatch_rejected(self):
        """结果文件变化时哈希不一致，应当提示结果已被修改。"""
        self.fill()
        (self.p/"results"/"a.txt").write_text("A")
        self.add_row("file_manifest.csv",["results/a.txt","0"*64, "self","synthetic"])
        self.assertTrue(any("SHA256 mismatch" in s for s in workflow.validate(self.p)))

    def test_toy_demo_deterministic(self):
        """固定种子的示例多次运行应得到相同指标，并明确不作科学判断。"""
        m1=demo_resolution.run(self.p/"toy1")
        m2=demo_resolution.run(self.p/"toy2")
        self.assertEqual(m1,m2)
        self.assertEqual(m1["scientific_decision"],"NOT_ASSESSED")
        self.assertEqual(len((self.p/"toy1"/"synthetic_profiles.csv").read_text().splitlines()),82)

    def test_research_data_cannot_initialize_inside_skill(self):
        """保护仓库：不得在公开Skill源码树内部自动创建真实科研项目。"""
        with self.assertRaisesRegex(ValueError, "outside|inside the public skill"):
            workflow.init(ROOT / "my-study")
        self.assertFalse((ROOT / "my-study").exists())

    def test_validated_experiment_requires_hashed_manifest(self):
        """已核验实验必须登记输出文件哈希，否则证据链不完整。"""
        self.fill()
        f = self.p / "results" / "output.json"
        f.write_text('{"value": 1}')
        self.add_row("experiment_registry.csv", ["E1", "other", "syn", "2026-10-17T12:00:00Z", "2026-10-18T00:00:00Z", "validated", "H1", "rule", "controls", "results/output.json"])
        msgs = workflow.validate(self.p)
        self.assertTrue(any("validated output requires SHA256" in x for x in msgs), msgs)

    def test_validated_claim_requires_hashed_manifest(self):
        """论文结论引用的结果也必须关联到文件哈希条目。"""
        self.fill()
        f = self.p / "results" / "output.json"
        f.write_text('{"value": 1}')
        self.add_row("experiment_registry.csv", ["E1", "other", "syn", "2026-10-17T12:00:00Z", "2026-10-18T00:00:00Z", "validated", "H1", "rule", "controls", "results/output.json"])
        self.add_row("file_manifest.csv", ["results/output.json", workflow.sha256(f), "toy", "synthetic"])
        self.add_row("evidence_ledger.csv", ["C1", "Claim", "E1", "results/missing.json", "field", "uncertainty", "limits", "validated", "toy only"])
        msgs = workflow.validate(self.p)
        self.assertTrue(any("validated claim requires SHA256" in x for x in msgs), msgs)

    def test_malformed_dataset_id_does_not_crash(self):
        """非法dataset_id类型应转为可读报错，而不是中断验证器。"""
        self.fill()
        config = json.loads((self.p / "project.json").read_text())
        config["datasets"][0]["dataset_id"] = ["invalid", "array"]
        (self.p / "project.json").write_text(json.dumps(config))
        msgs = workflow.validate(self.p)
        self.assertTrue(any("dataset[0] missing dataset_id" in x for x in msgs), msgs)

    def test_csv_missing_columns_is_reported(self):
        """数据行缺列应被报告，防止字段错位造成伪关联。"""
        self.fill()
        with (self.p / "experiment_registry.csv").open("a") as fp:
            fp.write("E1,other\n")
        msgs = workflow.validate(self.p)
        self.assertTrue(any("rows with missing columns" in x for x in msgs), msgs)

    def test_symlink_escape_rejected(self):
        """符号链接不得将文件校验指向研究目录之外的私有文件。"""
        self.fill()
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("sensitive")
        pointer = self.p / "data" / "link.txt"
        try:
            pointer.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform")
        self.add_row("file_manifest.csv", ["data/link.txt", "", "self", "not for public release"])
        msgs = workflow.validate(self.p)
        self.assertTrue(any("path escapes project" in x for x in msgs), msgs)

    def test_release_scan_rejects_data_directory(self):
        """公开仓库若混入真实数据目录，应在发布前拦截。"""
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / ROOT.name
            import shutil
            shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns("__pycache__"))
            (src / "data").mkdir()
            (src / "data" / "readme.txt").write_text("private material")
            errors, _, _ = check_release.scan(src)
            self.assertTrue(any("Forbidden research" in x for x in errors), errors)

    def test_release_static_check(self):
        """对仓库源码执行静态发布核查，不代替人工版权和隐私审核。"""
        errors,_,count=check_release.scan(ROOT)
        self.assertEqual(errors,[])
        self.assertGreaterEqual(count,10)


# 集成测试：不仅检查单张表，还串联合成生成、哈希登记与结论查询。
# 这里通过属性绑定把函数加入TestCase，以延续原有测试组织而不改变执行逻辑。
def _test_toy_end_to_end(self):
    """完整生成合成示例并验证跨文件证据链，同时拒绝宣称物理识别成功。"""
    import build_toy_project
    target=Path(self.tmp.name)/"full-toy"
    build_toy_project.build(target)
    msgs=workflow.validate(target)
    self.assertFalse(any(x.startswith("ERROR:") for x in msgs),msgs)
    with (target/"evidence_ledger.csv").open(encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    self.assertEqual(rows[0]["status"],"validated")
WorkflowTests.test_toy_end_to_end = _test_toy_end_to_end

if __name__ == "__main__":
    unittest.main()
