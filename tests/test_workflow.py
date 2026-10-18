"""Regression checks for the validator and deterministic synthetic-only demo."""
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
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)/"study"
        workflow.init(self.p)

    def fill(self):
        p=self.p/"project.json"
        config=json.loads(p.read_text())
        config.update(project_id="toy-study",research_question="Can a toy blur distinguish two 1D forms?",status="active",updated_utc="2026-10-18T00:00:00Z")
        config["spatial_context"]={"crs":"EPSG:4326","horizontal_domain":"86-94 E (toy)","vertical_datum":"not_applicable","depth_positive":"down","units":"arbitrary signal units"}
        config["datasets"]=[{"dataset_id":"syn","role":"observation","name":"Synthetic illustrative observation","source":"generated locally by deterministic script","version":"v1","license_notes":"original synthetic only"}]
        p.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding="utf-8")

    def add_row(self,filename, values):
        with (self.p/filename).open("a",encoding="utf-8",newline="") as f:
            writer=csv.writer(f);writer.writerow(values)

    def test_incomplete_template_fails(self):
        self.assertTrue(any(x.startswith("ERROR:") for x in workflow.validate(self.p)))

    def test_structural_valid_without_claims_not_scientific_validation(self):
        self.fill()
        m=workflow.validate(self.p)
        self.assertFalse(any(x.startswith("ERROR:") for x in m),m)
        self.assertTrue(any("WARN: empty evidence" in x for x in m))

    def test_prior_in_gravity_only_rejected(self):
        self.fill()
        j=json.loads((self.p/"project.json").read_text())
        j["datasets"].append({"dataset_id":"external","role":"prior","name":"Prior density","source":"toy","version":"v1","license_notes":"toy"})
        (self.p/"project.json").write_text(json.dumps(j))
        self.add_row("experiment_registry.csv",["E1","gravity_only","syn|external","2026-10-17T12:00:00Z","","planned","H1","frozen rule","controls",""])
        m=workflow.validate(self.p)
        self.assertTrue(any("gravity_only uses" in x for x in m),m)

    def test_claim_without_evidence_rejected(self):
        self.fill()
        (self.p/"results").mkdir(exist_ok=True)
        (self.p/"results"/"example.json").write_text('{}')
        self.add_row("experiment_registry.csv",["E1","other","syn","2026-10-17T12:00:00Z","2026-10-18T00:00:00Z","validated","H1","rule","controls","results/example.json"])
        self.add_row("evidence_ledger.csv",["C1","Claim","E1","results/missing.json","row1","uncertainty","limits","validated","conditional"])
        m=workflow.validate(self.p)
        self.assertTrue(any("does not exist" in x for x in m),m)

    def test_registration_after_execution_fails(self):
        self.fill()
        self.add_row("experiment_registry.csv",["E1","other","syn","2026-10-19T00:00:00Z","2026-10-18T00:00:00Z","failed","H1","rule","controls",""])
        m=workflow.validate(self.p)
        self.assertTrue(any("after execution" in x for x in m),m)

    def test_path_traversal_rejected(self):
        self.fill()
        self.add_row("file_manifest.csv",["../../private.txt","", "self","private"])
        self.assertTrue(any("unsafe path" in s for s in workflow.validate(self.p)))

    def test_hash_mismatch_rejected(self):
        self.fill()
        (self.p/"results"/"a.txt").write_text("A")
        self.add_row("file_manifest.csv",["results/a.txt","0"*64, "self","synthetic"])
        self.assertTrue(any("SHA256 mismatch" in s for s in workflow.validate(self.p)))

    def test_toy_demo_deterministic(self):
        m1=demo_resolution.run(self.p/"toy1")
        m2=demo_resolution.run(self.p/"toy2")
        self.assertEqual(m1,m2)
        self.assertEqual(m1["scientific_decision"],"NOT_ASSESSED")
        self.assertEqual(len((self.p/"toy1"/"synthetic_profiles.csv").read_text().splitlines()),82)

    def test_research_data_cannot_initialize_inside_skill(self):
        with self.assertRaisesRegex(ValueError, "outside|inside the public skill"):
            workflow.init(ROOT / "my-study")
        self.assertFalse((ROOT / "my-study").exists())

    def test_validated_experiment_requires_hashed_manifest(self):
        self.fill()
        f = self.p / "results" / "output.json"
        f.write_text('{"value": 1}')
        self.add_row("experiment_registry.csv", ["E1", "other", "syn", "2026-10-17T12:00:00Z", "2026-10-18T00:00:00Z", "validated", "H1", "rule", "controls", "results/output.json"])
        msgs = workflow.validate(self.p)
        self.assertTrue(any("validated output requires SHA256" in x for x in msgs), msgs)

    def test_validated_claim_requires_hashed_manifest(self):
        self.fill()
        f = self.p / "results" / "output.json"
        f.write_text('{"value": 1}')
        self.add_row("experiment_registry.csv", ["E1", "other", "syn", "2026-10-17T12:00:00Z", "2026-10-18T00:00:00Z", "validated", "H1", "rule", "controls", "results/output.json"])
        self.add_row("file_manifest.csv", ["results/output.json", workflow.sha256(f), "toy", "synthetic"])
        self.add_row("evidence_ledger.csv", ["C1", "Claim", "E1", "results/missing.json", "field", "uncertainty", "limits", "validated", "toy only"])
        msgs = workflow.validate(self.p)
        self.assertTrue(any("validated claim requires SHA256" in x for x in msgs), msgs)

    def test_malformed_dataset_id_does_not_crash(self):
        self.fill()
        config = json.loads((self.p / "project.json").read_text())
        config["datasets"][0]["dataset_id"] = ["invalid", "array"]
        (self.p / "project.json").write_text(json.dumps(config))
        msgs = workflow.validate(self.p)
        self.assertTrue(any("dataset[0] missing dataset_id" in x for x in msgs), msgs)

    def test_csv_missing_columns_is_reported(self):
        self.fill()
        with (self.p / "experiment_registry.csv").open("a") as fp:
            fp.write("E1,other\n")
        msgs = workflow.validate(self.p)
        self.assertTrue(any("rows with missing columns" in x for x in msgs), msgs)

    def test_symlink_escape_rejected(self):
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
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / ROOT.name
            import shutil
            shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns("__pycache__"))
            (src / "data").mkdir()
            (src / "data" / "readme.txt").write_text("private material")
            errors, _, _ = check_release.scan(src)
            self.assertTrue(any("Forbidden research" in x for x in errors), errors)

    def test_release_static_check(self):
        errors,_,count=check_release.scan(ROOT)
        self.assertEqual(errors,[])
        self.assertGreaterEqual(count,10)


# Integrated generated example check.
def _test_toy_end_to_end(self):
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
