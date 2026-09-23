import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import unittest

from tools.paper_tables import build_tables as tables


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(os.environ.get("PAPER_TABLES_TEST_OUTPUT", ROOT / "out/paper_tables_tests")).resolve()
VSI = "vsibench_answerable500"
VSTI = "vstibench_repr450_v2"


class TableTests(unittest.TestCase):
    def setUp(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="case_", dir=OUTPUT))

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def fixture(self, *, benchmark=VSI, condition="base", seed=17,
                strict_credit=0.2, lenient_credit=0.8, protocol="trinity", reference=False, paired=True):
        name = f"{benchmark}_{condition}_{seed}"
        score_dir = self.root / name / "scores/base"
        rescore_dir = self.root / name / "lenient"
        rows = [{"qid": str(index), "category": category, "credit": strict_credit,
                 "parsed_answer": "1", "canonical_metrics": {"is_correct": False}}
                for index, category in enumerate(tables.BENCHMARKS[benchmark].categories)]
        strict = tables.recompute(rows, benchmark)
        replay = [{"qid": row["qid"], "category": row["category"],
                   "strict_credit": strict_credit, "lenient_credit": lenient_credit,
                   "strict_answer": "1", "lenient_answer": "2"} for row in rows]
        lenient = tables.recompute(replay, benchmark, "lenient_credit", "lenient_answer")
        score_dir.mkdir(parents=True)
        raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
        (score_dir / "per_question_scores.jsonl").write_bytes(raw)
        recorded = {"benchmark": benchmark, "metric": tables.BENCHMARKS[benchmark].metric,
                    "category_scores": strict.categories, "primary_score": strict.overall,
                    "raw_category_macro": strict.macro, "parse_failures": 0,
                    "coverage_complete": True, "official_aggregation_complete": True,
                    "expected_count": len(rows), "terminal_count": len(rows), "missing_count": 0,
                    "cap_count": 0, "cap_without_answer_count": 0,
                    "per_question_scores": {"sha256": hashlib.sha256(raw).hexdigest(),
                                            "size_bytes": len(raw)}}
        self.write_json(score_dir / "scores.json", recorded)
        def summary(result):
            return {"category_scores": result.categories, "primary_score": result.overall,
                    "raw_category_macro": result.macro, "parse_failures": 0}
        self.write_json(rescore_dir / "lenient_scores.json", {"cells": {name: {
            "benchmark": benchmark, "metric": recorded["metric"], "items": len(rows),
            "scores_dir": str(score_dir), "strict": summary(strict), "lenient": summary(lenient)}}})
        if paired:
            (rescore_dir / f"per_question_{name}.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in replay), encoding="utf-8")
        return {"student": "onethinker_8b", "benchmark": benchmark, "condition": condition,
                "seed": seed, "strict_score_path": str(score_dir),
                "lenient_score_path": str(rescore_dir / "lenient_scores.json"),
                "lenient_cell_key": name, "harness_commit": "synthetic",
                "status": "complete", "protocol": protocol, "reference_only": reference,
                "provenance_note": "Synthetic fixture; no model or external service.",
                "doc_aliases": ["base" if condition == "base" else "arm C"]}

    def pending(self, condition="full_scale", seed=17):
        return {"student": "onethinker_8b", "benchmark": VSI, "condition": condition,
                "seed": seed, "strict_score_path": None, "lenient_score_path": None,
                "lenient_cell_key": None, "harness_commit": None, "status": "pending",
                "protocol": "orchard", "reference_only": False, "provenance_note": "Awaiting scores."}

    def test_per_type_uses_fractional_credit_not_correct_flag(self):
        cell = tables.load_cell(self.fixture())
        self.assertAlmostEqual(cell.strict.categories["object_counting"], 0.2)
        self.assertAlmostEqual(cell.strict.overall, 0.2)
        self.assertEqual(cell.strict.counts["object_counting"], 1)

    def test_official_vsi_groups_direction_instead_of_raw_macro(self):
        rows = [{"qid": str(i), "category": category,
                 "credit": float(category.startswith("object_rel_direction")), "parsed_answer": "A"}
                for i, category in enumerate(tables.BENCHMARKS[VSI].categories)]
        result = tables.recompute(rows, VSI)
        self.assertAlmostEqual(result.overall, 1 / 8)
        self.assertAlmostEqual(result.macro, 3 / 10)

    def test_official_vsti_collapses_both_three_type_groups(self):
        rows = [{"qid": str(i), "category": category,
                 "credit": float(category.startswith("obj_obj_relative_pos")), "parsed_answer": "A"}
                for i, category in enumerate(tables.BENCHMARKS[VSTI].categories)]
        result = tables.recompute(rows, VSTI)
        self.assertAlmostEqual(result.overall, 1 / 5)
        self.assertAlmostEqual(result.macro, 1 / 3)

    def test_lenient_and_strict_selection(self):
        cell = tables.load_cell(self.fixture())
        self.assertAlmostEqual(cell.strict.overall, 0.2)
        self.assertAlmostEqual(cell.lenient.overall, 0.8)
        self.assertIn("80.00", tables.render_accuracy([cell], VSI, "lenient"))
        self.assertIn("20.00", tables.render_accuracy([cell], VSI, "strict"))

    def test_duplicate_qids_and_nonfinite_credits_are_rejected(self):
        rows = [{"qid": str(i), "category": c, "credit": 0.5, "parsed_answer": "A"}
                for i, c in enumerate(tables.BENCHMARKS[VSI].categories)]
        with self.assertRaises(tables.ScoreError):
            tables.recompute(rows + [rows[0]], VSI)
        rows[0]["credit"] = float("nan")
        with self.assertRaises(tables.ScoreError):
            tables.recompute(rows, VSI)

    def test_missing_category_is_rejected(self):
        with self.assertRaises(tables.ScoreError):
            tables.recompute([{"qid": "a", "category": "object_counting", "credit": 0.5,
                               "parsed_answer": "1"}], VSI)

    def test_stored_score_mismatch_is_rejected(self):
        entry = self.fixture()
        path = Path(entry["strict_score_path"]) / "scores.json"
        recorded = json.loads(path.read_text())
        recorded["category_scores"]["object_counting"] = 0.9
        self.write_json(path, recorded)
        with self.assertRaisesRegex(tables.ScoreError, "object_counting"):
            tables.load_cell(entry)

    def test_lenient_score_mismatch_is_rejected(self):
        entry = self.fixture()
        path = Path(entry["lenient_score_path"])
        recorded = json.loads(path.read_text())
        recorded["cells"][entry["lenient_cell_key"]]["lenient"]["primary_score"] = 0.9
        self.write_json(path, recorded)
        with self.assertRaisesRegex(tables.ScoreError, "primary_score"):
            tables.load_cell(entry)

    def test_strict_pin_mismatch_is_rejected(self):
        entry = self.fixture()
        path = Path(entry["strict_score_path"]) / "scores.json"
        recorded = json.loads(path.read_text())
        recorded["per_question_scores"]["sha256"] = "0" * 64
        self.write_json(path, recorded)
        with self.assertRaisesRegex(tables.ScoreError, "sha256"):
            tables.load_cell(entry)

    def test_mean_range_and_sample_standard_deviation(self):
        cells = [tables.load_cell(self.fixture(condition="armc", seed=seed, lenient_credit=value))
                 for seed, value in [(17, 0.1), ("rep2", 0.2), ("rep3", 0.4)]]
        result = tables.seed_summary(cells)
        self.assertAlmostEqual(result["mean"], statistics.mean([10, 20, 40]))
        self.assertAlmostEqual(result["range"], 30)
        self.assertAlmostEqual(result["sample_std"], statistics.stdev([10, 20, 40]))
        rendered = tables.render_accuracy(cells, VSI, "lenient")
        self.assertIn(r"\makebox[", rendered)
        self.assertNotIn("r@{}l", rendered)

    def test_pending_cells_render_without_opening_paths(self):
        pending = tables.load_cell(self.pending())
        rendered = tables.render_accuracy([pending], VSI, "lenient")
        self.assertIn("Full-scale", rendered)
        self.assertIn("--", rendered)
        self.assertNotIn(r"\textbf{--}", rendered)

    def test_pending_replicate_does_not_become_zero(self):
        cell = tables.load_cell(self.fixture(condition="armc", lenient_credit=0.8))
        pending = self.pending("armc", "rep2")
        pending["protocol"] = "trinity"
        result = tables.seed_summary([cell, tables.load_cell(pending)])
        self.assertEqual(result["mean"], 80)
        self.assertIsNone(result["sample_std"])
        self.assertEqual(result["n"], 1)
        self.assertIsNone(result["rep2"])

    def test_latex_escaping(self):
        self.assertEqual(tables.latex_escape("seed_rep2 & 10%"), r"seed\_rep2 \& 10\%")
        entry = self.fixture()
        entry["label"] = "base_test"
        rendered = tables.render_accuracy([tables.load_cell(entry)], VSI, "lenient")
        self.assertIn(r"base\_test", rendered)

    def test_reference_rows_do_not_enter_main_or_best_marks(self):
        base = tables.load_cell(self.fixture(lenient_credit=0.4))
        armc = tables.load_cell(self.fixture(condition="armc", lenient_credit=0.8))
        ref = tables.load_cell(self.fixture(condition="r6_formatA", lenient_credit=1, reference=True))
        main = tables.render_accuracy([base, armc, ref], VSI, "lenient")
        self.assertNotIn("100.00", main)
        self.assertIn(r"\textbf{80.00}", main)
        appendix = tables.render_accuracy([ref], VSI, "lenient", references=True)
        self.assertIn("100.00", appendix)
        self.assertNotIn(r"\textbf{100.00}", appendix)

    def test_document_checker_covers_headline_and_unavailable_median(self):
        cell = tables.load_cell(self.fixture())
        doc = self.root / "document.md"
        doc.write_text("## OneThinker-8B\n### VSIBench\n"
                       "| cell | lenient (primary, %) | strict (secondary, %) | parse failures (strict → lenient) | cap-hit | cap without answer | median gen tokens | terminal |\n"
                       "|---|---|---|---|---|---|---|---|---|\n"
                       "| base | 80.00 | 20.00 | 0 → 0 | 0 | 0 | 9 | 10/10 |\n", encoding="utf-8")
        report = tables.check_document(doc, [cell])
        self.assertEqual(report.checked, 9)
        self.assertEqual(len(report.issues), 1)
        self.assertIn("median", report.issues[0].quantity)
        self.assertIsNone(report.issues[0].computed)

    def test_document_checker_reports_all_wrong_numbers(self):
        cell = tables.load_cell(self.fixture())
        doc = self.root / "wrong.md"
        doc.write_text("## OneThinker-8B\n### VSIBench\n"
                       "| question type | base |\n|---|---|\n"
                       "| object_counting | 19.00 |\n| **macro over raw categories** | 21.00 |\n",
                       encoding="utf-8")
        report = tables.check_document(doc, [cell])
        self.assertEqual(len(report.issues), 2)
        self.assertEqual({issue.computed for issue in report.issues}, {20.0})

    def test_document_delta_uses_unrounded_scores(self):
        base = tables.load_cell(self.fixture(lenient_credit=0.15475))
        armc = tables.load_cell(self.fixture(condition="armc", lenient_credit=0.4925))
        doc = self.root / "delta.md"
        expected = (armc.lenient.overall - base.lenient.overall) * 100
        doc.write_text("## OneThinker-8B\n### VSIBench\n"
                       "| quantity | base | arm C | delta |\n|---|---|---|---|\n"
                       f"| primary score, lenient (%) | {base.lenient.overall * 100:.2f} | {armc.lenient.overall * 100:.2f} | {expected:.2f} |\n",
                       encoding="utf-8")
        self.assertFalse(tables.check_document(doc, [base, armc]).issues)

    def test_unmapped_numeric_column_fails_closed(self):
        cell = tables.load_cell(self.fixture())
        doc = self.root / "unknown.md"
        doc.write_text("## OneThinker-8B\n### VSIBench\n"
                       "| question type | base | mystery |\n|---|---|---|\n"
                       "| object_counting | 20 | 30 |\n", encoding="utf-8")
        report = tables.check_document(doc, [cell])
        self.assertEqual(len(report.issues), 1)
        self.assertIn("mystery", report.issues[0].quantity)

    def test_render_does_not_overwrite_edited_caption_macros(self):
        cells = [tables.load_cell(self.fixture())]
        out = self.root / "tables"
        tables.render_all(cells, out)
        captions = out / "tables_captions.tex"
        text = captions.read_text().replace("Base", "Author wording")
        captions.write_text(text, encoding="utf-8")
        tables.render_all(cells, out)
        self.assertEqual(captions.read_text(), text)
        self.assertTrue((out / "tables_captions.generated.tex").is_file())

    def test_render_refuses_score_directory(self):
        entry = self.fixture()
        with self.assertRaises(tables.ScoreError):
            tables.render_all([tables.load_cell(entry)], Path(entry["strict_score_path"]))

    def test_lenient_summary_fallback_is_explicit_and_validated(self):
        entry = self.fixture(paired=False)
        cell = tables.load_cell(entry)
        self.assertFalse(cell.lenient_recomputed)
        self.assertAlmostEqual(cell.lenient.overall, 0.8)
        self.assertIsNone(cell.lenient.failures)
        path = Path(entry["lenient_score_path"])
        record = json.loads(path.read_text())
        record["cells"][entry["lenient_cell_key"]]["lenient"]["category_scores"]["object_counting"] = 1.2
        self.write_json(path, record)
        with self.assertRaisesRegex(tables.ScoreError, "fractions"):
            tables.load_cell(entry)

    def test_lenient_membership_and_strict_replay_are_checked(self):
        entry = self.fixture()
        path = Path(entry["lenient_score_path"]).with_name(f"per_question_{entry['lenient_cell_key']}.jsonl")
        rows = tables.read_jsonl(path)
        rows[0]["strict_credit"] = 0.3
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        with self.assertRaisesRegex(tables.ScoreError, "strict replay differs"):
            tables.load_cell(entry)
        rows[0]["strict_credit"] = 0.2
        rows[0]["qid"] = "foreign"
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        with self.assertRaisesRegex(tables.ScoreError, "membership differs"):
            tables.load_cell(entry)

    def test_parse_failures_are_not_incorrect_answer_counts(self):
        rows = [{"qid": str(i), "category": category, "credit": 0.0, "parsed_answer": "A"}
                for i, category in enumerate(tables.BENCHMARKS[VSI].categories)]
        rows[0]["parsed_answer"] = None
        result = tables.recompute(rows, VSI)
        self.assertEqual(result.parse_failures, 1)
        self.assertEqual(result.failures[rows[0]["category"]], 1)
        self.assertEqual(result.overall, 0)

    def test_generation_counts_and_optional_median_come_from_scores(self):
        entry = self.fixture()
        path = Path(entry["strict_score_path"]) / "scores.json"
        record = json.loads(path.read_text())
        record.update(cap_count=3, cap_without_answer_count=2, median_gen_tokens=17)
        self.write_json(path, record)
        cell = tables.load_cell(entry)
        self.assertEqual(tables.raw_quantity(cell, "cap"), 3)
        self.assertEqual(tables.raw_quantity(cell, "cap_without"), 2)
        self.assertEqual(tables.raw_quantity(cell, "median"), 17)
        record["cap_count"] = 2.5
        self.write_json(path, record)
        with self.assertRaisesRegex(tables.ScoreError, "invalid count"):
            tables.load_cell(entry)

    def test_incomplete_or_mismatched_metric_is_rejected(self):
        entry = self.fixture()
        path = Path(entry["strict_score_path"]) / "scores.json"
        record = json.loads(path.read_text())
        record["coverage_complete"] = False
        self.write_json(path, record)
        with self.assertRaisesRegex(tables.ScoreError, "coverage"):
            tables.load_cell(entry)
        record["coverage_complete"] = True
        record["metric"] = "raw-category-macro"
        self.write_json(path, record)
        with self.assertRaisesRegex(tables.ScoreError, "metric"):
            tables.load_cell(entry)

    def test_pending_fill_requires_only_manifest_fields_and_rerun(self):
        complete = self.fixture(condition="full_scale", protocol="orchard")
        pending = self.pending()
        pending["harness_commit"] = complete["harness_commit"]
        path = self.root / "manifest.json"
        self.write_json(path, {"schema": "split-paper-tables-v1", "cells": [pending]})
        self.assertFalse(tables.load_manifest(path)[0].complete)
        for key in ("status", "strict_score_path", "lenient_score_path", "lenient_cell_key"):
            pending[key] = complete[key]
        self.write_json(path, {"schema": "split-paper-tables-v1", "cells": [pending]})
        rendered = tables.render_accuracy(tables.load_manifest(path), VSI, "lenient")
        self.assertIn("Full-scale", rendered)
        self.assertIn("80.00", rendered)

    def test_orchard_values_cannot_change_trinity_best_marks(self):
        base = tables.load_cell(self.fixture(lenient_credit=0.4))
        armc = tables.load_cell(self.fixture(condition="armc", lenient_credit=0.8))
        orchard = tables.load_cell(self.fixture(condition="orchard_base", protocol="orchard", lenient_credit=0.99))
        rendered = tables.render_accuracy([base, armc, orchard], VSI, "lenient")
        self.assertIn(r"\textbf{80.00}", rendered)
        self.assertNotIn(r"\textbf{99.00}", rendered)

    def test_seed_rounding_difference_is_reported_not_corrected(self):
        cells = [tables.load_cell(self.fixture(condition="armc", seed=seed, lenient_credit=score))
                 for seed, score in [(17, 0.4925), ("rep2", 0.487916666666667)]]
        doc = self.root / "rounding.md"
        rounded_std = statistics.stdev([round(cell.lenient.overall * 100, 2) for cell in cells])
        doc.write_text("## OneThinker-8B\n### VSIBench\n"
                       "| benchmark | sample std |\n|---|---|\n"
                       f"| VSIBench | {rounded_std:.2f} |\n", encoding="utf-8")
        report = tables.check_document(doc, cells)
        self.assertEqual(len(report.issues), 1)
        self.assertIn("already rounded", report.issues[0].cause)
        self.assertAlmostEqual(report.issues[0].computed, tables.seed_summary(cells)["sample_std"])

    def test_seed_summary_rejects_duplicate_identifiers(self):
        cell = tables.load_cell(self.fixture(condition="armc"))
        with self.assertRaisesRegex(tables.ScoreError, "duplicate"):
            tables.seed_summary([cell, cell])

    def test_cli_exit_status_for_matching_and_mismatching_document(self):
        entry = self.fixture()
        manifest = self.root / "manifest.json"
        doc = self.root / "cli.md"
        self.write_json(manifest, {"schema": "split-paper-tables-v1", "cells": [entry]})
        args = ["--manifest", str(manifest), "--check-doc", str(doc)]
        for value, code in [(20, 0), (21, 1)]:
            with self.subTest(value=value), contextlib.redirect_stdout(io.StringIO()):
                doc.write_text("## OneThinker-8B\n### VSIBench\n"
                               "| question type | base |\n|---|---|\n"
                               f"| object_counting | {value} |\n", encoding="utf-8")
                self.assertEqual(tables.main(args), code)

    def test_output_symlink_cannot_overwrite_a_score_file(self):
        entry = self.fixture()
        cell = tables.load_cell(entry)
        score = Path(entry["strict_score_path"]) / "scores.json"
        before = score.read_bytes()
        out = self.root / "unsafe"
        out.mkdir()
        (out / "main_vsi.tex").symlink_to(score)
        with self.assertRaisesRegex(tables.ScoreError, "symlink"):
            tables.render_all([cell], out)
        self.assertEqual(score.read_bytes(), before)

    def test_unedited_caption_defaults_refresh_and_pending_claims_stay_cautious(self):
        base = tables.load_cell(self.fixture())
        out = self.root / "refresh"
        tables.render_all([base], out)
        first = (out / "tables_captions.tex").read_text()
        armc = tables.load_cell(self.fixture(condition="armc", lenient_credit=0.95))
        tables.render_all([base, armc], out)
        second = (out / "tables_captions.tex").read_text()
        self.assertNotEqual(first, second)
        self.assertEqual(second, (out / "tables_captions.generated.tex").read_text())
        self.assertIn("await complete scores", tables.caption_defaults([tables.load_cell(self.pending())]))

    @unittest.skipUnless(shutil.which("pdflatex"), "pdflatex is not on PATH")
    def test_rendered_tables_compile(self):
        cells = [tables.load_cell(self.fixture(benchmark=benchmark, condition=condition))
                 for benchmark in [VSI, VSTI] for condition in ["base", "armc"]]
        cells.append(tables.load_cell(self.pending()))
        out = self.root / "compiled"
        tables.render_all(cells, out)
        tables.compile_preview(out)
        self.assertGreater((out / "tables_preview.pdf").stat().st_size, 0)


class RealManifestTests(unittest.TestCase):
    def test_real_manifest_reproduces_document(self):
        try:
            cells = tables.load_manifest(ROOT / "tools/paper_tables/manifest.json")
        except OSError as exc:
            self.skipTest(f"Score path is unreadable: {exc}")
        report = tables.check_document(ROOT / "docs/RESULTS_PER_TYPE_20260922.md", cells)
        self.assertGreater(report.checked, 500)
        if report.issues:
            self.fail(report.format_text())

    def test_real_manifest_replays_all_available_question_scores(self):
        try:
            cells = tables.load_manifest(ROOT / "tools/paper_tables/manifest.json")
        except OSError as exc:
            self.skipTest(f"Score path is unreadable: {exc}")
        completed = [cell for cell in cells if cell.complete]
        self.assertTrue(completed)
        for cell in completed:
            with self.subTest(cell=cell.identity):
                self.assertTrue(cell.lenient_recomputed)
                self.assertEqual(sum(cell.strict.counts.values()), cell.recorded["expected_count"])


if __name__ == "__main__":
    unittest.main()
