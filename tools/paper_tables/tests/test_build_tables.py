import contextlib
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import tempfile
import unittest
from unittest.mock import patch

from tools.paper_tables import build_tables as tables


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(os.environ.get("PAPER_TABLES_TEST_OUTPUT", ROOT / "out/paper_tables_tests")).resolve()
VSI = "vsibench_answerable500"
VSTI = "vstibench_repr450_v2"
VSI_FULL = "vsibench_full5130"
SCOPES = {
    VSI: "VSIBench-500 (answerable subset, 50 per category; not comparable to published full-benchmark numbers)",
    VSTI: "VSTIBench-450 (representative subset, 50 per category)",
    VSI_FULL: "VSI-Bench full (5,130 questions, official metric)",
}


def assert_scope_captions(test, out):
    checked = {}
    for path in sorted(out.glob("*.tex")):
        text = path.read_text(encoding="utf-8")
        if r"\begin{table" not in text:
            continue
        with test.subTest(table=path.name):
            captions = [line for line in text.splitlines() if line.startswith(r"\caption{")]
            test.assertEqual(len(captions), 1)
            test.assertEqual(text.count(r"\begin{table"), 1)
            benchmarks = set(re.findall(r"^% cell=[^/\n]+/([^/\n]+)/", text, re.MULTILINE))
            test.assertTrue(benchmarks, "A generated score table must identify its source cells")
            for benchmark in benchmarks:
                test.assertIn(tables.latex_escape(tables.BENCHMARKS[benchmark].scope_label), captions[0])
            checked[path.name] = benchmarks
    test.assertTrue(checked)
    return checked


class TableTests(unittest.TestCase):
    def setUp(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="case_", dir=OUTPUT))

    def write_json(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def fixture(self, *, benchmark=VSI, condition="base", seed=17,
                strict_credit=0.2, lenient_credit=0.8, protocol="trinity", reference=False,
                paired=True, empty_items=0, items_per_category=1, empty_offset=0):
        name = f"{benchmark}_{condition}_{seed}"
        score_dir = self.root / name / "scores/base"
        rescore_dir = self.root / name / "lenient"
        counts = (items_per_category if isinstance(items_per_category, dict)
                  else dict.fromkeys(tables.BENCHMARKS[benchmark].categories, items_per_category))
        categories = [category for category in tables.BENCHMARKS[benchmark].categories
                      for _ in range(counts[category])]
        empty_indices = range(empty_offset, empty_offset + empty_items)
        rows = [{"qid": str(index), "category": category,
                 "credit": 0 if index in empty_indices else strict_credit,
                 "parsed_answer": None if index in empty_indices else "1",
                 "status": "media_error" if index in empty_indices else "ok",
                 "canonical_metrics": {"is_correct": False}}
                for index, category in enumerate(categories)]
        strict = tables.recompute(rows, benchmark)
        lenient_credits = lenient_credit if isinstance(lenient_credit, dict) else dict.fromkeys(categories, lenient_credit)
        replay = [{"qid": row["qid"], "category": row["category"],
                   "strict_credit": row["credit"],
                   "lenient_credit": lenient_credits[row["category"]] if row["status"] == "ok" else 0,
                   "strict_answer": row["parsed_answer"], "lenient_answer": "2" if row["status"] == "ok" else None}
                  for row in rows]
        lenient = tables.recompute(replay, benchmark, "lenient_credit", "lenient_answer")
        score_dir.mkdir(parents=True)
        raw = "".join(json.dumps(row) + "\n" for row in rows).encode()
        (score_dir / "per_question_scores.jsonl").write_bytes(raw)
        recorded = {"benchmark": benchmark, "metric": tables.BENCHMARKS[benchmark].metric,
                    "category_scores": strict.categories, "primary_score": strict.overall,
                    "raw_category_macro": strict.macro, "parse_failures": strict.parse_failures,
                    "coverage_complete": True, "official_aggregation_complete": True,
                    "expected_count": len(rows), "terminal_count": len(rows), "missing_count": 0,
                    "cap_count": 0, "cap_without_answer_count": 0,
                    "failure_counts": dict(tables.Counter(row["status"] for row in rows)),
                    "per_question_scores": {"sha256": hashlib.sha256(raw).hexdigest(),
                                            "size_bytes": len(raw)}}
        self.write_json(score_dir / "scores.json", recorded)
        def summary(result):
            return {"category_scores": result.categories, "primary_score": result.overall,
                    "raw_category_macro": result.macro, "parse_failures": result.parse_failures}
        self.write_json(rescore_dir / "lenient_scores.json", {"cells": {name: {
            "benchmark": benchmark, "metric": recorded["metric"], "items": len(rows),
            "scores_dir": str(score_dir), "strict": summary(strict), "lenient": summary(lenient)}}})
        if paired:
            (rescore_dir / f"per_question_{name}.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in replay), encoding="utf-8")
        orchard = protocol in {"orchard", "thinking_off_reference"}
        commit = "12e477b" if orchard else "58794b8"
        base = "base_27b_thinkoff" if condition == "base_27b_thinkoff" else "orchard_base" if orchard else "base"
        return {"student": "onethinker_8b", "benchmark": benchmark, "condition": condition,
                "seed": seed, "strict_score_path": str(score_dir),
                "lenient_score_path": str(rescore_dir / "lenient_scores.json"),
                "lenient_cell_key": name, "harness_commit": commit,
                "harness": f"{'orchard' if orchard else 'trinity'}-{commit}", "base_ref": base,
                "status": "complete", "protocol": protocol, "reference_only": reference,
                "provisional": bool(empty_items), "empty_items": empty_items,
                "empty_statuses": ["media_error"] if empty_items else [],
                "provenance_note": "Synthetic fixture; no model or external service."}

    def pending(self, condition="full_scale", seed=17, protocol="orchard"):
        orchard = protocol == "orchard"
        commit = "12e477b" if orchard else "58794b8"
        return {"student": "onethinker_8b", "benchmark": VSI, "condition": condition,
                "seed": seed, "strict_score_path": None, "lenient_score_path": None,
                "lenient_cell_key": None, "harness_commit": commit, "status": "pending",
                "harness": f"{protocol}-{commit}", "base_ref": "orchard_base" if orchard else "base",
                "protocol": protocol, "reference_only": False, "provenance_note": "Awaiting scores."}

    def test_benchmark_scope_specifications(self):
        for benchmark, scope in SCOPES.items():
            with self.subTest(benchmark=benchmark):
                self.assertEqual(tables.BENCHMARKS[benchmark].scope_label, scope)
        subset, full = tables.BENCHMARKS[VSI], tables.BENCHMARKS[VSI_FULL]
        self.assertEqual((full.categories, full.labels, full.metric, full.groups),
                         (subset.categories, subset.labels, subset.metric, subset.groups))
        self.assertNotEqual(full.short, subset.short)

    def test_full_benchmark_unequal_counts_and_official_aggregate(self):
        counts = dict(zip(tables.BENCHMARKS[VSI_FULL].categories,
                          [401, 421, 441, 461, 481, 501, 521, 541, 561, 801]))
        credits = {category: float(category.startswith("object_rel_direction")) for category in counts}
        credits["object_counting"] = 0.4
        entries = [self.fixture(benchmark=benchmark, condition=condition)
                   for benchmark in (VSI, VSTI) for condition in ("base", "armc")]
        entries.extend(self.fixture(benchmark=VSI_FULL, condition=condition, items_per_category=counts,
                                    lenient_credit=credits, reference=condition == "r6_formatA")
                       for condition in ("base", "armc", "r6_formatA"))
        manifest = self.root / "manifest.json"
        self.write_json(manifest, {"schema": "split-paper-tables-v1", "cells": entries})
        cells = tables.load_manifest(manifest)
        full = next(cell for cell in cells if cell.entry["benchmark"] == VSI_FULL)
        self.assertEqual(full.recorded["expected_count"], 5130)
        self.assertEqual(full.lenient.counts, counts)
        self.assertAlmostEqual(full.lenient.overall, (1 + 0.4) / 8)
        self.assertAlmostEqual(full.lenient.macro, (3 + 0.4) / 10)
        weighted = sum(credits[category] * count for category, count in counts.items()) / sum(counts.values())
        self.assertNotAlmostEqual(full.lenient.overall, weighted)
        out = self.root / "full_tables"
        files = tables.render_all(cells, out)
        self.assertIn("main_vsi.tex", files)
        self.assertIn("main_vsifull.tex", files)
        for name in ("main_vsifull.tex", "appendix_vsifull_strict.tex",
                     "appendix_vsifull_seeds_lenient.tex", "appendix_vsifull_seeds_strict.tex",
                     "appendix_vsifull_references_lenient.tex", "appendix_vsifull_references_strict.tex"):
            with self.subTest(table=name):
                text = (out / name).read_text(encoding="utf-8")
                self.assertIn(SCOPES[VSI_FULL], text)
                self.assertNotIn("50 per category", text)
                rows = [line for line in text.splitlines() if "($n=" in line]
                self.assertTrue(rows)
                for row in rows:
                    self.assertEqual([int(n) for n in re.findall(r"\(\$n=(\d+)\$\)", row)],
                                     [*counts.values(), sum(counts.values())])
        text = (out / "main_vsifull.tex").read_text(encoding="utf-8")
        self.assertIn(r"\captakeawayVSIFull{}", text)
        base_row = next(line for line in text.splitlines() if line.startswith("Base &"))
        self.assertEqual(re.findall(r"& (?:\\textbf\{)?(\d+\.\d+)", base_row)[-1], "17.50")
        subset = (out / "main_vsi.tex").read_text(encoding="utf-8")
        self.assertNotIn(SCOPES[VSI_FULL], subset)
        self.assertNotIn("($n=", subset)
        macros = (out / "tables_captions.tex").read_text(encoding="utf-8")
        self.assertIn(r"\newcommand{\captakeawayVSI}", macros)
        self.assertIn(r"\newcommand{\captakeawayVSIFull}", macros)
        checked = assert_scope_captions(self, out)
        self.assertEqual(checked["appendix_seed_summaries.tex"], set(SCOPES))

    def test_full_benchmark_requires_visible_manifest_cells(self):
        base = tables.load_cell(self.fixture())
        omitted = tables.load_cell({**self.pending("base", protocol="trinity"),
                                    "benchmark": VSI_FULL, "table": "omit"})
        out = self.root / "subset_only"
        files = tables.render_all([base, omitted], out)
        self.assertFalse(any("vsifull" in name for name in files))
        self.assertNotIn("VSIFull", (out / "tables_captions.tex").read_text(encoding="utf-8"))
        self.assertNotIn(SCOPES[VSI_FULL], (out / "tables_preview.tex").read_text(encoding="utf-8"))
        assert_scope_captions(self, out)
        pending = tables.load_cell({**omitted.entry, "table": "main"})
        pending_out = self.root / "full_pending"
        files = tables.render_all([base, pending], pending_out)
        self.assertIn("main_vsifull.tex", files)
        text = (pending_out / "main_vsifull.tex").read_text(encoding="utf-8")
        self.assertIn("($n=--$)", text)
        self.assertNotIn("($n=5130$)", text)
        assert_scope_captions(self, pending_out)

    def test_full_benchmark_counts_follow_matched_views(self):
        counts = {category: index + 2 for index, category in enumerate(tables.BENCHMARKS[VSI_FULL].categories)}
        cells = [tables.load_cell(self.fixture(benchmark=VSI_FULL, condition=condition,
                                              items_per_category=counts, empty_items=int(condition == "base")))
                 for condition in ("base", "armc")]
        text = tables.render_accuracy(cells, VSI_FULL, "lenient", matched_primary=True)
        for prefix, total, first_count in (("Arm C, matched", 64, 1), ("Arm C, all", 65, 2)):
            row = next(line for line in text.splitlines() if line.startswith(prefix))
            self.assertEqual([int(n) for n in re.findall(r"\(\$n=(\d+)\$\)", row)],
                             [first_count, *list(counts.values())[1:], total])
        self.assertIn(SCOPES[VSI_FULL], text)

    def test_full_benchmark_validates_each_cells_expected_count(self):
        counts = {category: index + 1 for index, category in enumerate(tables.BENCHMARKS[VSI_FULL].categories)}
        entry = self.fixture(benchmark=VSI_FULL, items_per_category=counts)
        cell = tables.load_cell(entry)
        self.assertEqual(cell.recorded["expected_count"], 55)
        self.assertEqual(sum(cell.strict.counts.values()), 55)
        path = Path(entry["strict_score_path"]) / "scores.json"
        recorded = json.loads(path.read_text(encoding="utf-8"))
        for expected in (500, 5130):
            with self.subTest(expected=expected):
                self.write_json(path, {**recorded, "expected_count": expected})
                with self.assertRaisesRegex(tables.ScoreError, "coverage contract"):
                    tables.load_cell(entry)
        self.write_json(path, recorded)
        path = Path(entry["lenient_score_path"])
        rescore = json.loads(path.read_text(encoding="utf-8"))
        rescore["cells"][entry["lenient_cell_key"]]["items"] = 500
        self.write_json(path, rescore)
        with self.assertRaisesRegex(tables.ScoreError, "identity/coverage"):
            tables.load_cell(entry)

    def test_scope_labels_survive_edited_caption_macros(self):
        cell = tables.load_cell(self.fixture())
        out = self.root / "edited_captions"
        tables.render_all([cell], out)
        captions = out / "tables_captions.tex"
        text = captions.read_text(encoding="utf-8").replace(tables.MAIN_TABLE_CAPTION, "Author wording.")
        captions.write_text(text, encoding="utf-8")
        tables.render_all([cell], out)
        self.assertEqual(captions.read_text(encoding="utf-8"), text)
        assert_scope_captions(self, out)

    @unittest.skipUnless(shutil.which("pdflatex"), "pdflatex is not on PATH")
    def test_scope_labels_with_tex_metacharacters_compile(self):
        label = "Full_scope & 100% {audited} #1 $metric$ ~ ^ \\ scope"
        spec = replace(tables.BENCHMARKS[VSI_FULL], scope_label=label)
        with patch.dict(tables.BENCHMARKS, {VSI_FULL: spec}):
            counts = {category: index + 2 for index, category in enumerate(spec.categories)}
            cells = [tables.load_cell(self.fixture(benchmark=VSI_FULL, condition=condition,
                                                  items_per_category=counts, empty_items=int(condition == "base")))
                     for condition in ("base", "armc")]
            out = self.root / "full_compiled"
            tables.render_all(cells, out)
            assert_scope_captions(self, out)
            self.assertTrue(tables.compile_preview(out))
            self.assertGreater((out / "tables_preview.pdf").stat().st_size, 0)

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
        rendered = tables.render_accuracy([tables.load_cell(self.fixture()), *cells], VSI, "lenient")
        self.assertIn(r"\makebox[", rendered)
        self.assertNotIn("r@{}l", rendered)

    def test_pending_cells_render_without_opening_paths(self):
        pending = tables.load_cell(self.pending())
        rendered = tables.render_accuracy([tables.load_cell(self.pending("orchard_base")), pending], VSI, "lenient")
        self.assertIn("Full-scale", rendered)
        self.assertIn("--", rendered)
        self.assertNotIn(r"\textbf{--}", rendered)

    def test_table_field_filters_main_and_appendix_rows(self):
        base = tables.load_cell(self.fixture())
        appendix_entry = self.fixture(condition="armc")
        appendix_entry["table"] = "appendix"
        omitted_entry = self.fixture(condition="answer_only")
        omitted_entry["table"] = "omit"
        appendix = tables.load_cell(appendix_entry)
        omitted = tables.load_cell(omitted_entry)
        cells = [base, appendix, omitted]
        main = tables.render_accuracy(tables.cells_for_table(cells, "main"), VSI, "lenient")
        appendix_text = tables.render_accuracy(tables.cells_for_table(cells, "appendix"), VSI, "lenient")
        self.assertEqual(base.entry["table"], "main")
        self.assertIn("Base &", main)
        self.assertNotIn("Arm C", main)
        self.assertNotIn("Answer-only control", main)
        self.assertIn("Arm C", appendix_text)
        self.assertNotIn("Answer-only control", appendix_text)
        with self.assertRaisesRegex(tables.ScoreError, "table"):
            tables.load_cell({**self.fixture(condition="setb_pilot"), "table": "supplement"})

    def test_pending_replicate_does_not_become_zero(self):
        cell = tables.load_cell(self.fixture(condition="armc", lenient_credit=0.8))
        pending = self.pending("armc", "rep2", protocol="trinity")
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

    def test_document_checker_excludes_named_raw_category_from_macro(self):
        cell = tables.load_cell(self.fixture())
        rows = [{"qid": category, "category": category,
                 "credit": 0.9 if category == "room_size_estimation" else 0.2,
                 "parsed_answer": "1"}
                for category in tables.BENCHMARKS[VSI].categories]
        cell.strict = tables.recompute(rows, VSI)
        doc = self.root / "excluded_macro.md"
        doc.write_text("## OneThinker-8B\n### VSIBench\n"
                       "| question type | base |\n|---|---|\n"
                       "| macro over raw categories, excl. `room_size_estimation` | 20.00 |\n",
                       encoding="utf-8")
        self.assertFalse(tables.check_document(doc, [cell]).issues)

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

    def test_document_delta_vs_arm_c_is_not_substituted_with_base_delta(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, strict_credit=0.2))
        armc = tables.load_cell(self.fixture(benchmark=VSTI, condition="armc", strict_credit=0.5))
        for cell in (base, armc):
            cell.entry["student"] = "qwen35_9b"
        doc = self.root / "arm_c_delta.md"
        doc.write_text("## Qwen3.5-9B\n### VSTIBench — Set B pilot, Orchard\n"
                       "| question type | delta vs arm C |\n|---|---|\n"
                       "| camera_displacement | -4.20 |\n", encoding="utf-8")
        report = tables.check_document(doc, [base, armc])
        self.assertEqual(len(report.issues), 1)
        self.assertIsNone(report.issues[0].computed)
        self.assertEqual(report.issues[0].cause, "cross-harness reference column")

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
        base = self.fixture(condition="orchard_base", protocol="orchard")
        pending = self.pending()
        path = self.root / "manifest.json"
        self.write_json(path, {"schema": "split-paper-tables-v1", "cells": [pending, base]})
        self.assertFalse(tables.load_manifest(path)[0].complete)
        for key in ("status", "strict_score_path", "lenient_score_path", "lenient_cell_key"):
            pending[key] = complete[key]
        self.write_json(path, {"schema": "split-paper-tables-v1", "cells": [pending, base]})
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
        cells.extend(tables.load_cell(self.pending(condition)) for condition in ("orchard_base", "full_scale"))
        out = self.root / "compiled"
        tables.render_all(cells, out)
        tables.compile_preview(out)
        self.assertGreater((out / "tables_preview.pdf").stat().st_size, 0)

    def test_manifest_requires_harness_and_base_ref(self):
        entry = self.fixture()
        for key in ("harness", "base_ref"):
            with self.subTest(key=key), self.assertRaisesRegex(tables.ScoreError, key):
                tables.load_cell({name: value for name, value in entry.items() if name != key})

    def test_harness_must_match_commit_and_protocol(self):
        entry = self.fixture()
        for update in ({"harness": "unknown"}, {"harness_commit": "12e477b"}, {"protocol": "orchard"},
                       {"harness": "trinity-unknown", "harness_commit": "372da10"},
                       {"harness": "trinity-372da10", "harness_commit": "58794b8"}):
            with self.subTest(update=update), self.assertRaisesRegex(tables.ScoreError, "harness"):
                tables.load_cell({**entry, **update})

    def test_codeaws_harness_loads_complete_cell(self):
        entry = self.fixture()
        for student in ("qwen35_9b", "qwen36_27b"):
            with self.subTest(student=student):
                cell = tables.load_cell({**entry, "student": student,
                                         "harness": "trinity-372da10", "harness_commit": "372da10"})
                self.assertTrue(cell.complete)
                self.assertTrue(cell.lenient_recomputed)
                self.assertEqual(cell.entry["harness"], "trinity-372da10")
                self.assertEqual(cell.entry["harness_commit"], "372da10")
                self.assertEqual(cell.identity, f"{student}/{VSI}/base/17/trinity-372da10")

    def test_manifest_distinguishes_harnesses_and_pairs_each_base(self):
        entries = [self.fixture(condition="base", empty_items=1, items_per_category=2),
                   self.fixture(condition="answer_only", items_per_category=2)]
        entries += [{**entry, "harness": "trinity-372da10", "harness_commit": "372da10"} for entry in entries]
        manifest = self.root / "manifest.json"
        self.write_json(manifest, {"schema": "split-paper-tables-v1", "cells": entries})
        cells = tables.load_manifest(manifest)
        self.assertEqual(len(cells), 4)
        self.assertEqual(len({cell.identity for cell in cells}), 4)
        for base, student in (cells[:2], cells[2:]):
            with self.subTest(harness=base.entry["harness"]):
                self.assertIs(tables.paired_base(base, cells), base)
                self.assertIs(tables.paired_base(student, cells), base)
                self.assertIn(f"cell={student.identity}", tables.provenance(student))
        groups = tables.matched_groups(cells, VSI)
        self.assertEqual({group[0].identity for group in groups}, {cells[0].identity, cells[2].identity})
        self.assertEqual(len(tables.condition_groups(cells, VSI)), 4)
        self.assertEqual(tables.provisional_clause(cells).count("1/20 empty items"), 2)

    def test_manifest_rejects_duplicate_identity_on_same_harness(self):
        entry = self.pending("base", protocol="trinity")
        manifest = self.root / "manifest.json"
        self.write_json(manifest, {"schema": "split-paper-tables-v1", "cells": [entry, entry]})
        with self.assertRaisesRegex(tables.ScoreError, "Duplicate manifest cell identity"):
            tables.load_manifest(manifest)

    def test_base_pairing_rejects_cross_harness_reference(self):
        base = tables.load_cell(self.fixture())
        entry = self.fixture(condition="setb_pilot", protocol="orchard")
        entry["base_ref"] = "base"
        pilot = tables.load_cell(entry)
        with self.assertRaisesRegex(tables.ScoreError, "harness"):
            tables.paired_base(pilot, [base, pilot])

    def test_documented_cross_commit_pairing_requires_matching_decode_settings(self):
        base_entry = self.fixture(condition="orchard_base", protocol="orchard")
        base_entry.update({"harness": "orchard-12e477b-b16",
                           "decode_settings": {"batch_size": 16, "token_cap": 4096}})
        student_entry = self.fixture(condition="full_scale", protocol="orchard")
        student_entry.update({"harness_commit": "0ab73f9", "harness": "orchard-0ab73f9-b16",
                              "base_ref": "orchard_base",
                              "decode_settings": {"batch_size": 16, "token_cap": 4096},
                              "cross_commit_pairing": {
                                  "base_harness": "orchard-12e477b-b16",
                                  "decode_settings": {"batch_size": 16, "token_cap": 4096},
                              }})
        base, student = tables.load_cell(base_entry), tables.load_cell(student_entry)
        other_base = tables.load_cell({**base_entry, "harness": student.entry["harness"],
                                      "harness_commit": student.entry["harness_commit"]})
        cells = [other_base, base, student]
        self.assertIs(tables.paired_base(student, cells), base)
        student.entry["decode_settings"]["token_cap"] = 8192
        with self.assertRaisesRegex(tables.ScoreError, "matching decode settings"):
            tables.paired_base(student, cells)

    def test_manifest_rejects_missing_or_pending_base_for_complete_cell(self):
        pilot = self.fixture(condition="setb_pilot", protocol="orchard")
        manifest = self.root / "manifest.json"
        for entries in ([pilot], [self.pending("orchard_base"), pilot]):
            self.write_json(manifest, {"schema": "split-paper-tables-v1", "cells": entries})
            with self.subTest(entries=len(entries)), self.assertRaisesRegex(tables.ScoreError, "base"):
                tables.load_manifest(manifest)

    def test_each_condition_shows_its_same_harness_base(self):
        cells = [tables.load_cell(self.fixture(lenient_credit=0.4)),
                 tables.load_cell(self.fixture(condition="armc", lenient_credit=0.8)),
                 tables.load_cell(self.fixture(condition="orchard_base", protocol="orchard", lenient_credit=0.6)),
                 tables.load_cell(self.fixture(condition="setb_pilot", protocol="orchard", lenient_credit=0.7))]
        rendered = tables.render_accuracy(cells, VSI, "lenient")
        armc = next(line for line in rendered.splitlines() if line.startswith("Arm C &"))
        pilot = next(line for line in rendered.splitlines() if line.startswith("Set B pilot &"))
        self.assertTrue(armc.startswith("Arm C & 40.00 &"))
        self.assertTrue(pilot.startswith("Set B pilot & 60.00 &"))
        self.assertIn(r"\textbf{80.00}", armc)
        self.assertIn(r"\textbf{70.00}", pilot)

    def test_repeat_summary_rejects_mixed_harnesses(self):
        cells = [tables.load_cell(self.fixture(condition="armc")),
                 tables.load_cell(self.fixture(condition="armc", seed="rep2", protocol="orchard"))]
        with self.assertRaisesRegex(tables.ScoreError, "harness|cohort"):
            tables.seed_summary(cells)

    def test_provisional_flag_and_empty_count_are_validated(self):
        entry = self.fixture()
        for update in ({"provisional": "true"}, {"empty_items": True}, {"empty_items": -1},
                       {"empty_items": 1}, {"empty_statuses": ["ok"]}):
            with self.subTest(update=update), self.assertRaises(tables.ScoreError):
                tables.load_cell({**entry, **update})

    def test_empty_count_is_verified_against_score_statuses(self):
        entry = self.fixture(condition="orchard_base", protocol="orchard", empty_items=1)
        cell = tables.load_cell(entry)
        self.assertEqual(cell.empty_qids, frozenset({"0"}))
        self.assertEqual(cell.entry["empty_items"], 1)
        self.assertEqual(cell.recorded["expected_count"], 10)
        with self.assertRaisesRegex(tables.ScoreError, "empty"):
            tables.load_cell({**entry, "empty_items": 2})

    def test_provisional_dagger_keeps_full_denominator_and_marks_base_column(self):
        base = tables.load_cell(self.fixture(condition="orchard_base", protocol="orchard", empty_items=1))
        pilot = tables.load_cell(self.fixture(condition="setb_pilot", protocol="orchard"))
        rendered = tables.render_accuracy([base, pilot], VSI, "lenient")
        self.assertIn("Base (Orchard), all 10 (base lower bound", rendered)
        self.assertIn("1/10", rendered)
        self.assertIn("provisional", rendered)
        self.assertIn("full denominator", rendered)
        pilot_row = next(line for line in rendered.splitlines() if line.startswith("Set B pilot, all 10"))
        self.assertIn(f"{base.lenient.overall * 100:.2f}" + r"$^{\dagger}$", pilot_row)
        self.assertEqual(sum(base.strict.counts.values()), 10)
        for renderer in (tables.render_diagnostics, tables.render_macros):
            self.assertIn(r"Base (Orchard)$^{\dagger}$", renderer([base, pilot], VSI))

    def test_matched_view_excludes_only_the_bases_empty_qids_from_both_cells(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=2))
        pilot = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                             empty_items=2, items_per_category=2))
        self.assertEqual(tables.raw_quantity(base, "n", excluded=base.empty_qids), 17)
        self.assertEqual(tables.raw_quantity(pilot, "n", excluded=base.empty_qids), 17)
        self.assertAlmostEqual(tables.raw_quantity(pilot, "score", "lenient", excluded=base.empty_qids), 0.64)
        self.assertEqual(tables.raw_quantity(pilot, "parse", "lenient", excluded=base.empty_qids), 1)
        self.assertEqual(tables.raw_quantity(pilot, "n"), 18)

    def test_document_matched_per_type_uses_base_empty_qids(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            strict_credit=0.2, lenient_credit=0.2,
                                            empty_items=1, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               strict_credit=0.6, lenient_credit=0.6, items_per_category=2))
        doc = self.root / "matched_per_type.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench, Orchard\n"
                       "#### Per question type, matched 17-item cohort\n"
                       "| question type | Base | Distilled |\n|---|---|---|\n"
                       "| camera_displacement | 20 | 60 |\n", encoding="utf-8")
        report = tables.check_document(doc, [base, student])
        self.assertEqual(report.checked, 2)
        self.assertFalse(report.issues, report.format_text())

    def test_document_per_type_all_denominator_is_not_matched_subset(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            strict_credit=0.2, lenient_credit=0.2,
                                            empty_items=1, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               strict_credit=0.6, lenient_credit=0.6, items_per_category=2))
        doc = self.root / "all_denominator.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench, Orchard\n"
                       "#### Per question type, matched 17-item cohort and all 18 items\n"
                       "| question type | Base, all 18 | Distilled, all 18 |\n|---|---|---|\n"
                       "| camera_displacement | 10 | 60 |\n", encoding="utf-8")
        report = tables.check_document(doc, [base, student])
        self.assertEqual(report.checked, 2)
        self.assertFalse(report.issues, report.format_text())

    def test_document_checker_reads_interrupted_count(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard"))
        doc = self.root / "interrupted.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench, Orchard\n"
                       "| cell | cap-hit | interrupted |\n|---|---|---|\n"
                       "| Orchard base | 0 | 0 |\n", encoding="utf-8")
        report = tables.check_document(doc, [base])
        self.assertEqual(report.checked, 2)
        self.assertFalse(report.issues, report.format_text())

    def test_student_side_empty_qids_drive_matched_main_and_appendix_views(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            strict_credit=0.2, lenient_credit=0.2, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               strict_credit=0.6, lenient_credit=0.6, empty_items=1, items_per_category=2))
        cells = [base, student]
        excluded = tables.matched_excluded_qids(base, student)
        self.assertEqual(excluded, student.empty_qids)
        self.assertEqual(tables.raw_quantity(base, "n", excluded=excluded), 17)
        self.assertAlmostEqual(tables.raw_quantity(base, "score", "lenient", excluded=excluded), 0.2)
        self.assertAlmostEqual(tables.raw_quantity(student, "score", "lenient", excluded=excluded), 0.6)
        main = tables.render_accuracy(cells, VSTI, "lenient", matched_primary=True)
        appendix = tables.render_matched(cells, VSTI)
        strict = tables.render_accuracy(cells, VSTI, "strict")
        self.assertIn(r"Set B pilot, matched 17/18$^{\dagger}$ & 20.00", main)
        self.assertIn(r"Set B pilot$^{\dagger}$ & 17 & 60.00", appendix)
        self.assertIn(r"Set B pilot, all 18 lower bound$^{\dagger}$ & 20.00", strict)

    def test_base_side_empty_qids_drive_matched_primary_and_labelled_all_item_rows(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            strict_credit=0.2, lenient_credit=0.4,
                                            empty_items=1, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               strict_credit=0.6, lenient_credit=0.8, items_per_category=2))
        cells = [base, student]
        self.assertFalse(base.entry["main_matched"])
        self.assertFalse(student.entry["main_matched"])
        self.assertEqual(tables.matched_excluded_qids(base, student), frozenset({"0"}))
        for mode, base_score, student_score, all_base_score in (("lenient", "40.00", "80.00", "36.00"),
                                                               ("strict", "20.00", "60.00", "18.00")):
            with self.subTest(mode=mode):
                rendered = tables.render_accuracy(cells, VSTI, mode, matched_primary=True)
                matched = [line for line in rendered.splitlines() if line.startswith("Set B pilot, matched")]
                lower = [line for line in rendered.splitlines() if line.startswith("Set B pilot, all")]
                self.assertEqual(len(matched), 1)
                self.assertEqual(len(lower), 1)
                self.assertIn("matched 17/18", matched[0])
                self.assertIn(f" & {base_score}" + r"$^{\dagger}$", matched[0])
                self.assertIn(r"\textbf{" + student_score + "}", matched[0])
                self.assertIn("all 18", lower[0])
                self.assertIn("base lower bound", lower[0])
                self.assertIn(r"base media\_error counted wrong", lower[0])
                self.assertIn("delta upper bound", lower[0])
                self.assertIn(f" & {all_base_score}" + r"$^{\dagger}$", lower[0])
                self.assertNotIn(r"\textbf", lower[0])
                self.assertLess(rendered.index(matched[0]), rendered.index(lower[0]))
        self.assertEqual(tables.raw_quantity(base, "n"), 18)
        self.assertEqual(tables.raw_quantity(student, "n"), 18)

    def test_two_sided_exclusions_use_the_union_without_bounding_the_delta(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            strict_credit=0.2, lenient_credit=0.2,
                                            empty_items=2, items_per_category=4))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               strict_credit=0.6, lenient_credit=0.6,
                                               empty_items=2, empty_offset=1, items_per_category=4))
        cells = [base, student]
        excluded = tables.matched_excluded_qids(base, student)
        self.assertEqual(excluded, frozenset({"0", "1", "2"}))
        self.assertEqual(tables.matched_excluded_qids(student, base), excluded)
        for cell, score in ((base, 0.2), (student, 0.6)):
            self.assertEqual(tables.raw_quantity(cell, "n", excluded=excluded), 33)
            self.assertAlmostEqual(tables.raw_quantity(cell, "score", "lenient", excluded=excluded), score)
        main = tables.render_accuracy(cells, VSTI, "lenient", matched_primary=True)
        self.assertIn(r"Set B pilot, matched 33/36$^{\dagger}$ & 20.00", main)
        lower = next(line for line in main.splitlines() if line.startswith("Set B pilot, all"))
        self.assertIn("base and student lower bounds", lower)
        self.assertIn("delta not bounded", lower)
        self.assertNotIn("delta upper bound", lower)
        appendix = tables.render_matched(cells, VSTI)
        self.assertIn(r"Base (Orchard)$^{\dagger}$ & 33 & 20.00", appendix)
        self.assertIn(r"Set B pilot$^{\dagger}$ & 33 & 60.00", appendix)
        self.assertIn("union", appendix)
        doc = self.root / "union.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench, Orchard\n"
                       "#### Matched-cohort comparison\n"
                       "| cell | lenient (%) | strict (%) |\n|---|---|---|\n"
                       "| Orchard base, matched 33/36 | 20 | 20 |\n"
                       "| Set B distilled (Orchard), matched 33/36 | 60 | 60 |\n", encoding="utf-8")
        report = tables.check_document(doc, cells)
        self.assertEqual(report.checked, 4)
        self.assertFalse(report.issues, report.format_text())

    def test_union_excluding_a_whole_category_fails_closed(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               empty_items=1, empty_offset=1, items_per_category=2))
        with self.assertRaisesRegex(tables.ScoreError, "category membership"):
            tables.render_accuracy([base, student], VSTI, "lenient", matched_primary=True)

    def test_base_side_exclusions_do_not_turn_pending_students_into_matched_scores(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=2))
        student = tables.load_cell({**self.pending("setb_pilot"), "benchmark": VSTI})
        rendered = tables.render_accuracy([base, student], VSTI, "lenient", matched_primary=True)
        row = next(line for line in rendered.splitlines() if line.startswith("Set B pilot &"))
        self.assertIn("--", row)
        self.assertNotIn("Set B pilot, matched", rendered)
        self.assertNotIn("Set B pilot, all", rendered)

    def test_document_matched_prose_delta_uses_unrounded_union_scores(self):
        for benchmark in (VSI, VSTI):
            with self.subTest(benchmark=benchmark):
                base = tables.load_cell(self.fixture(benchmark=benchmark, condition="orchard_base", protocol="orchard",
                                                    lenient_credit=0.194755, empty_items=2, items_per_category=4))
                student = tables.load_cell(self.fixture(benchmark=benchmark, condition="setb_pilot", protocol="orchard",
                                                       lenient_credit=0.46231, empty_items=2, empty_offset=1,
                                                       items_per_category=4))
                excluded = tables.matched_excluded_qids(base, student)
                self.assertEqual(excluded, frozenset({"0", "1", "2"}))
                count = len(base.strict.qids) - len(excluded)
                expected = (0.46231 - 0.194755) * 100
                doc = self.root / f"matched_delta_{benchmark}.md"
                for delta in ("+26.75", "+26.76"):
                    with self.subTest(delta=delta):
                        doc.write_text(f"## OneThinker-8B\n### {tables.BENCHMARKS[benchmark].name}\n"
                                       f"PRIMARY: on the matched {count}-item cohort, the student scores 46.23 "
                                       f"versus the base's 19.48, a {delta}-point gain.\n", encoding="utf-8")
                        report = tables.check_document(doc, [base, student])
                        self.assertEqual(report.checked, 1)
                        if delta == "+26.75":
                            self.assertEqual(len(report.issues), 1)
                            self.assertIn("Unrounded score-derived calculation differs", report.issues[0].cause)
                            self.assertAlmostEqual(report.issues[0].computed, expected)
                        else:
                            self.assertFalse(report.issues, report.format_text())

    def test_document_matched_prose_delta_uses_either_sides_exclusions(self):
        for benchmark, base_empty, student_empty in ((VSTI, 1, 0), (VSI, 0, 1)):
            with self.subTest(benchmark=benchmark):
                base = tables.load_cell(self.fixture(benchmark=benchmark, condition="orchard_base", protocol="orchard",
                                                    lenient_credit=0.2, empty_items=base_empty, items_per_category=2))
                student = tables.load_cell(self.fixture(benchmark=benchmark, condition="setb_pilot", protocol="orchard",
                                                       lenient_credit=0.6, empty_items=student_empty, items_per_category=2))
                count = len(base.strict.qids) - 1
                doc = self.root / f"one_sided_delta_{benchmark}.md"
                doc.write_text(f"## OneThinker-8B\n### {tables.BENCHMARKS[benchmark].name}\n"
                               f"PRIMARY: on the matched {count}-item cohort, the student scores 60.00 "
                               "versus the base's 20.00, a +40.00-point gain.\n"
                               "SECONDARY: on all items, the student has a +99.00-point gain.\n", encoding="utf-8")
                report = tables.check_document(doc, [base, student])
                self.assertEqual(report.checked, 1)
                self.assertFalse(report.issues, report.format_text())

    def test_document_matched_prose_delta_respects_strict_context_and_wrapping(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            strict_credit=0.5, lenient_credit=0.2, empty_items=1, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               strict_credit=0.3, lenient_credit=0.6, items_per_category=2))
        doc = self.root / "strict_matched_delta.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench\n#### Matched comparison (strict parser)\n"
                       "On the matched 17-item cohort, the student scores 30.00\n"
                       "versus the base's 50.00, a −20.00-point gain.\n", encoding="utf-8")
        report = tables.check_document(doc, [base, student])
        self.assertEqual(report.checked, 1)
        self.assertFalse(report.issues, report.format_text())

    def test_document_matched_prose_delta_rejects_ambiguous_pairs(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            lenient_credit=0.2, empty_items=1, items_per_category=2))
        students = [tables.load_cell(self.fixture(benchmark=VSTI, condition=condition, protocol="orchard",
                                                 lenient_credit=credit, items_per_category=2))
                    for condition, credit in (("setb_pilot", 0.6), ("full_scale", 0.8))]
        doc = self.root / "ambiguous_matched_delta.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench\n"
                       "On the matched 17-item cohort, the student scores 60.00 "
                       "versus the base's 20.00, a +40.00-point gain.\n", encoding="utf-8")
        report = tables.check_document(doc, [base, *students])
        self.assertEqual(report.checked, 1)
        self.assertEqual(len(report.issues), 1)
        self.assertIsNone(report.issues[0].computed)
        self.assertIn("2 pairs", report.issues[0].cause)

    def test_document_matched_prose_delta_rejects_wrong_count_and_missing_replay(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            lenient_credit=0.2, empty_items=1, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               lenient_credit=0.6, items_per_category=2))
        doc = self.root / "unavailable_matched_delta.md"
        for count, cause in ((16, "0 pairs"), (17, "per-question scores are unavailable")):
            with self.subTest(count=count):
                if count == 17:
                    student.lenient_rows = ()
                doc.write_text("## OneThinker-8B\n### VSTIBench\n"
                               f"On the matched {count}-item cohort, the student scores 60.00 "
                               "versus the base's 20.00, a +40.00-point gain.\n", encoding="utf-8")
                report = tables.check_document(doc, [base, student])
                self.assertEqual(report.checked, 1)
                self.assertEqual(len(report.issues), 1)
                self.assertIsNone(report.issues[0].computed)
                self.assertIn(cause, report.issues[0].cause)

    def test_document_matched_prose_delta_requires_audited_exclusions(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            lenient_credit=0.2, items_per_category=2))
        student = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                               lenient_credit=0.6, items_per_category=2))
        doc = self.root / "unaudited_matched_delta.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench\n"
                       "On the matched 18-item cohort, the student scores 60.00 "
                       "versus the base's 20.00, a +40.00-point gain.\n", encoding="utf-8")
        report = tables.check_document(doc, [base, student])
        self.assertEqual(report.checked, 1)
        self.assertEqual(len(report.issues), 1)
        self.assertIsNone(report.issues[0].computed)
        self.assertIn("0 pairs", report.issues[0].cause)

    def test_matched_view_requires_per_question_lenient_scores(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=2))
        pilot = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                             paired=False, items_per_category=2))
        with self.assertRaisesRegex(tables.QuantityUnavailable, "per-question"):
            tables.raw_quantity(pilot, "score", "lenient", excluded=base.empty_qids)

    def test_document_orchard_metadata_and_strict_deltas_use_matched_base(self):
        cells = [tables.load_cell(self.fixture(strict_credit=0.1, lenient_credit=0.95)),
                 tables.load_cell(self.fixture(condition="orchard_base", protocol="orchard")),
                 tables.load_cell(self.fixture(condition="setb_pilot", protocol="orchard", strict_credit=0.6, lenient_credit=0.6))]
        doc = self.root / "orchard.md"
        doc.write_text("## OneThinker-8B\n### VSIBench — Set B pilot, Orchard\n"
                       "| cell | harness | lenient (%) | strict (%) |\n|---|---|---|---|\n"
                       "| Set B distilled (Orchard) | orchard_trainer_12e477b | 60 | 60 |\n"
                       "| Orchard base | orchard_trainer_12e477b | 80 | 20 |\n"
                       "| trinity base | 58794b8 | 95 | 10 |\n"
                       "#### Per question type — strict parser only\n"
                       "| question type | Set B distilled (Orchard) | Orchard base | delta |\n|---|---|---|---|\n"
                       "| object_counting | 60 | 20 | 40 |\n", encoding="utf-8")
        report = tables.check_document(doc, cells)
        self.assertEqual(report.checked, 9)
        self.assertFalse(report.issues, report.format_text())

    def test_document_trinity_mean_row_uses_full_precision_repeats(self):
        cells = [tables.load_cell(self.fixture(condition="armc", seed=seed, lenient_credit=credit))
                 for seed, credit in [(17, 0.42), ("rep2", 0.43), ("rep3", 0.44)]]
        doc = self.root / "mean.md"
        doc.write_text("## OneThinker-8B\n### VSIBench — Set B pilot, Orchard\n"
                       "| cell | harness | lenient (%) |\n|---|---|---|\n"
                       "| trinity arm C, 3-seed mean | 58794b8 | 43.00 |\n", encoding="utf-8")
        report = tables.check_document(doc, cells)
        self.assertEqual(report.checked, 1)
        self.assertFalse(report.issues, report.format_text())

    def test_document_matched_macros_preserve_parser_labels(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=2))
        doc = self.root / "matched.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench — Set B pilot, Orchard\n"
                       "#### Matched-cohort comparison\n"
                       "| cell | lenient (%) | strict (%) | macro over categories (%) |\n|---|---|---|---|\n"
                       "| Orchard base, 17-item matched cohort | 80 | 20 | 80 (lenient) / 20 (strict) |\n", encoding="utf-8")
        report = tables.check_document(doc, [base])
        self.assertEqual(report.checked, 4)
        self.assertFalse(report.issues, report.format_text())

    def test_document_matched_headline_rejects_flat_question_mean(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=2))
        credits = {category: 0.4 if category == "camera_displacement" else 0.8
                   for category in tables.BENCHMARKS[VSTI].categories}
        pilot = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                             lenient_credit=credits, items_per_category=2))
        doc = self.root / "flat.md"
        doc.write_text("## OneThinker-8B\n### VSTIBench — Set B pilot, Orchard\n"
                       "#### Matched-cohort comparison\n"
                       "| cell | lenient (%) |\n|---|---|\n"
                       f"| Set B distilled (Orchard), 17-item matched cohort | {(40 + 16 * 80) / 17:.2f} |\n", encoding="utf-8")
        report = tables.check_document(doc, [base, pilot])
        self.assertEqual(len(report.issues), 1)
        self.assertAlmostEqual(report.issues[0].computed, 72)
        self.assertIn("flat", report.issues[0].cause)

    def test_document_cross_harness_delta_fails_closed(self):
        base = tables.load_cell(self.fixture())
        pilot = tables.load_cell(self.fixture(condition="setb_pilot", protocol="orchard"))
        doc = self.root / "cross_harness.md"
        doc.write_text("## OneThinker-8B\n### VSIBench — Set B pilot, Orchard\n"
                       "| question type | Set B distilled (Orchard) - trinity base delta |\n|---|---|\n"
                       "| object_counting | 0 |\n", encoding="utf-8")
        report = tables.check_document(doc, [base, pilot])
        self.assertEqual(len(report.issues), 1)
        self.assertIn("harness", report.issues[0].cause)

    def test_matched_appendix_uses_official_metric_without_changing_main_scores(self):
        base = tables.load_cell(self.fixture(benchmark=VSTI, condition="orchard_base", protocol="orchard",
                                            empty_items=1, items_per_category=3))
        pilot = tables.load_cell(self.fixture(benchmark=VSTI, condition="setb_pilot", protocol="orchard",
                                             empty_items=2, items_per_category=3))
        before = (base.lenient.overall, pilot.lenient.overall, base.recorded["expected_count"])
        rendered = tables.render_matched([base, pilot], VSTI)
        self.assertIn("Set B pilot" + r"$^{\dagger}$ & 25 & 80.00", rendered)
        self.assertIn("official category collapse", rendered)
        self.assertEqual(before, (base.lenient.overall, pilot.lenient.overall, base.recorded["expected_count"]))
        self.assertIsNone(tables.render_matched([base, pilot], VSI))

    @unittest.skipUnless(shutil.which("pdflatex"), "pdflatex is not on PATH")
    def test_provisional_and_matched_tables_compile(self):
        cells = [tables.load_cell(self.fixture(benchmark=VSTI, condition=condition, protocol="orchard",
                                              empty_items=int(condition == "orchard_base"), items_per_category=2))
                 for condition in ("orchard_base", "setb_pilot")]
        out = self.root / "provisional_compiled"
        files = tables.render_all(cells, out)
        self.assertIn("appendix_vsti_matched.tex", files)
        self.assertTrue(tables.compile_preview(out))
        self.assertGreater((out / "tables_preview.pdf").stat().st_size, 0)

    def test_document_qwen_vsti_two_run_summary_is_checked(self):
        cells = [tables.load_cell(self.fixture(benchmark=VSTI, condition="armc", seed=seed, lenient_credit=credit))
                 for seed, credit in [(17, 0.46), ("rep2", 0.42)]]
        for cell in cells:
            cell.entry["student"] = "qwen35_9b"
        doc = self.root / "qwen_repeats.md"
        doc.write_text("## Qwen3.5-9B\n### VSTIBench\n"
                       "| benchmark | published | replicate 2 | mean | range (max-min) | sample std |\n"
                       "|---|---|---|---|---|---|\n"
                       f"| VSTIBench | 46 | 42 | 44 | 4 | {statistics.stdev([46, 42]):.2f} |\n", encoding="utf-8")
        report = tables.check_document(doc, cells)
        self.assertEqual(report.checked, 5)
        self.assertFalse(report.issues, report.format_text())


class RealManifestTests(unittest.TestCase):
    def test_real_manifest_declared_cross_commit_pairs(self):
        try:
            cells = tables.load_manifest(ROOT / "tools/paper_tables/manifest.json")
        except OSError as exc:
            self.skipTest(f"Score path is unreadable: {exc}")
        declared = [cell for cell in cells if "cross_commit_pairing" in cell.entry]
        self.assertEqual(len(declared), 2)
        self.assertEqual({(cell.entry["student"], cell.entry["benchmark"], cell.entry["condition"]) for cell in declared},
                         {("qwen35_9b", VSI, "full_scale"), ("qwen35_9b", VSTI, "full_scale")})
        for cell in declared:
            with self.subTest(cell=cell.identity):
                base = tables.paired_base(cell, cells)
                self.assertEqual(base.entry["harness"], cell.entry["cross_commit_pairing"]["base_harness"])
                self.assertNotEqual(base.entry["harness"], cell.entry["harness"])
                self.assertEqual(base.entry["condition"], cell.entry["base_ref"])
                self.assertTrue(tables.documented_cross_commit_pairing(cell, base))

    def test_real_manifest_every_table_caption_names_its_benchmark_scopes(self):
        try:
            cells = tables.load_manifest(ROOT / "tools/paper_tables/manifest.json")
        except OSError as exc:
            self.skipTest(f"Score path is unreadable: {exc}")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix="real_scopes_", dir=OUTPUT))
        files = tables.render_all(cells, out)
        checked = assert_scope_captions(self, out)
        self.assertEqual(set(checked), set(files))
        visible = tables.cells_for_table(cells, "appendix")
        repeated = {cell.entry["benchmark"] for cell in visible
                    if cell.entry["condition"] == "armc" and not cell.reference}
        if repeated:
            self.assertEqual(checked["appendix_seed_summaries.tex"], repeated)
        for benchmark, spec in tables.BENCHMARKS.items():
            if not any(cell.entry["benchmark"] == benchmark for cell in visible):
                self.assertFalse(any(f"_{spec.short.lower()}." in name or f"_{spec.short.lower()}_" in name
                                     for name in files))

    def test_real_manifest_27b_base_interruptions_render_matched_and_all_item_rows(self):
        try:
            cells = tables.load_manifest(ROOT / "tools/paper_tables/manifest.json")
        except OSError as exc:
            self.skipTest(f"Score path is unreadable: {exc}")
        pair = {cell.entry["condition"]: cell for cell in cells
                if cell.entry["student"] == "qwen36_27b" and cell.entry["benchmark"] == VSTI}
        base, student = pair["base_27b_b8"], pair["armc_27b_b8"]
        self.assertIs(tables.paired_base(student, cells), base)
        self.assertEqual(base.entry["table"], "main")
        self.assertEqual(student.entry["table"], "main")
        self.assertEqual(base.empty_qids, frozenset({"4513", "4554", "4516", "4556", "4586", "4083", "3919", "4046",
                                                   "3800", "4182", "3916", "4111", "3159", "3411", "3714", "3174"}))
        self.assertFalse(student.empty_qids)
        excluded = tables.matched_excluded_qids(base, student)
        expected = {base.identity: (["1.20", "14.00", "18.60", "40.00", "46.00", "40.00", "64.00", "73.91", "83.72"],
                                    ["1.20", "14.00", "18.60", "36.00", "46.00", "40.00", "64.00", "68.00", "72.00"],
                                    "29.94", "28.49", 0.299355982473879),
                    student.identity: (["17.00", "36.00", "50.40", "66.67", "70.00", "74.00", "84.00", "84.78", "90.70"],
                                       ["17.00", "36.00", "50.40", "64.00", "70.00", "74.00", "84.00", "86.00", "92.00"],
                                       "52.02", "52.01", 0.520231299853949)}
        OUTPUT.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix="real_27b_", dir=OUTPUT))
        tables.render_all(cells, out)
        main = (out / "main_vsti.tex").read_text(encoding="utf-8")
        for cell in (base, student):
            with self.subTest(cell=cell.identity):
                per_type, all_per_type, overall, all_overall, unrounded = expected[cell.identity]
                matched_rows = [line for line in main.splitlines() if line.startswith(cell.label + ", matched")]
                all_rows = [line for line in main.splitlines() if line.startswith(cell.label + ", all")]
                self.assertEqual(len(matched_rows), 1)
                self.assertEqual(len(all_rows), 1)
                self.assertIn("matched 434/450", matched_rows[0])
                self.assertEqual(re.findall(r"& (?:\\textbf\{)?(\d+\.\d+)", matched_rows[0]),
                                 ["29.94", *per_type, overall])
                self.assertIn("all 450", all_rows[0])
                self.assertIn("base lower bound", all_rows[0])
                self.assertIn("base interrupted counted wrong", all_rows[0])
                self.assertEqual(re.findall(r"& (?:\\textbf\{)?(\d+\.\d+)", all_rows[0]),
                                 ["28.49", *all_per_type, all_overall])
                self.assertNotIn(r"\textbf", all_rows[0])
                self.assertLess(main.index(matched_rows[0]), main.index(all_rows[0]))
                self.assertEqual(tables.raw_quantity(cell, "n", excluded=excluded), 434)
                strict = tables.score_view(cell, "strict", excluded)
                lenient = tables.score_view(cell, "lenient", excluded)
                self.assertEqual(strict.categories, lenient.categories)
                self.assertAlmostEqual(lenient.overall, unrounded, places=14)
        student_all = next(line for line in main.splitlines() if line.startswith(student.label + ", all"))
        self.assertIn("delta upper bound", student_all)
        gain = (tables.score_view(student, "lenient", excluded).overall
                - tables.score_view(base, "lenient", excluded).overall) * 100
        self.assertEqual(f"{gain:.2f}", "22.09")

    def test_real_manifest_27b_matched_prose_delta_uses_unrounded_scores(self):
        manifest = json.loads((ROOT / "tools/paper_tables/manifest.json").read_text(encoding="utf-8"))
        entries = [entry for entry in manifest["cells"] if entry["student"] == "qwen36_27b"
                   and entry["benchmark"] == VSTI and entry["condition"] in {"base_27b_b8", "armc_27b_b8"}]
        self.assertEqual(len(entries), 2)
        try:
            cells = [tables.load_cell(entry) for entry in entries]
        except OSError as exc:
            self.skipTest(f"Score path is unreadable: {exc}")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="real_27b_prose_", dir=OUTPUT))
        for delta in ("+22.08", "+22.09"):
            with self.subTest(delta=delta):
                doc = root / f"matched_{delta}.md"
                doc.write_text("## Qwen3.6-27B\n### VSTIBench\n"
                               "| cell | lenient (%) |\n|---|---|\n"
                               "| Base (16 interrupted) | 28.49 |\n"
                               "| Arm C student (0 interrupted) | 52.01 |\n\n"
                               "PRIMARY: on the matched 434-item cohort, the student scores 52.02 "
                               f"versus the base's 29.94, a {delta}-point gain.\n", encoding="utf-8")
                report = tables.check_document(doc, cells)
                self.assertEqual(report.checked, 3)
                if delta == "+22.08":
                    self.assertEqual(len(report.issues), 1)
                    self.assertIn("Unrounded score-derived calculation differs", report.issues[0].cause)
                    self.assertAlmostEqual(report.issues[0].computed,
                                           (0.520231299853949 - 0.299355982473879) * 100)
                    self.assertEqual(report.issues[0].line, 8)
                else:
                    self.assertFalse(report.issues, report.format_text())

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
