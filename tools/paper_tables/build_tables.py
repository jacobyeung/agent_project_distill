"""Build auditable SPLIT tables without running a model or changing score artifacts.

 tools/paper_tables/README
 ========================
 Run from the repository root with Python 3.12 and the standard library::

     python -B -m tools.paper_tables.build_tables \
         --manifest tools/paper_tables/manifest.json --out /absolute/output/tables
     python -B -m tools.paper_tables.build_tables \
         --manifest tools/paper_tables/manifest.json \
         --check-doc docs/RESULTS_PER_TYPE_20260922.md \
         --mismatches /absolute/output/MISMATCHES.md
     CUDA_VISIBLE_DEVICES="" python -B -m unittest discover \
         -s tools/paper_tables/tests -v

 A pending cell needs only a manifest edit: set status to complete, supply its
 strict_score_path, lenient_score_path, lenient_cell_key, and harness_commit,
 then rerun the first command. Paths may be absolute or relative to the manifest.
 The rescorer's sibling per_question_<lenient_cell_key>.jsonl is read when present;
 lenient_per_question_path can explicitly name a different location. No parser
 is reimplemented, and raw generations, Markdown numbers, and results.csv are
 never metric inputs. Missing required score files are errors, not pending cells.

 Credits include each numeric item's mean relative accuracy, not its correct flag.
 Aggregation uses the official eight-task/five-subtask collapse groups and the
 scorer's decimal half-even mean at 15 places. Raw-category macro is separate.
 Stored aggregates must agree within 0.005 percentage points after two-decimal
 rounding. Seed statistics and deltas use unrounded scores; sample standard
 deviation uses n-1. Incomplete groups use completed runs only and expose n/N;
 one run has no sample standard deviation. Replicate IDs are not invented seeds.

 Input tables with \\input{...}; load tables_captions.tex once in the preamble.
 The floats need booktabs and graphicx. Captions retain author edits on rerun;
 tables_captions.generated.tex always contains fresh data-derived defaults.
 An untouched caption file updates automatically. Copy desired new defaults into
 an edited caption file yourself. Add --compile to compile tables_preview.tex
 when pdflatex is installed. TeX caches and logs stay under the output directory.

 --check-doc checks numeric result cells, not numeric prose in status/provenance
 tables. Unknown numeric columns fail closed. Unavailable quantities are reported
 rather than filled from the document; token medians are unavailable unless the
 score artifacts themselves contain token counts or a median. Any discrepancy
 gives exit status 1; malformed or unreadable score inputs give exit status 2.
 The real-manifest golden test deliberately fails on a document discrepancy and
 skips only if score files are unreadable. PAPER_TABLES_TEST_OUTPUT selects the
 retained synthetic-fixture directory; tests never delete their fixtures.

 These diagnostic artifacts remain provisional and ineligible for nomination.
 Reproduction and within-protocol table highlighting do not establish eligibility,
 significance, or a causal benefit. Orchard pilots pair only with Orchard bases;
 r6 and thinking-off references never enter main tables or best-value selection.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys


@dataclass(frozen=True)
class Benchmark:
    name: str
    short: str
    metric: str
    labels: dict[str, str]
    groups: tuple[tuple[str, ...], ...]

    @property
    def categories(self):
        return tuple(self.labels)


BENCHMARKS = {
    "vsibench_answerable500": Benchmark("VSIBench", "VSI", "vsibench-official-8task-v1", {
        "obj_appearance_order": "Order", "object_abs_distance": "Abs.Dist",
        "object_counting": "Count", "object_rel_direction_easy": "RelDir-E",
        "object_rel_direction_hard": "RelDir-H", "object_rel_direction_medium": "RelDir-M",
        "object_rel_distance": "Rel.Dist", "object_size_estimation": "Obj.Size",
        "room_size_estimation": "Room.Size", "route_planning": "Route",
    }, (("object_rel_direction_easy", "object_rel_direction_medium", "object_rel_direction_hard"),)),
    "vstibench_repr450_v2": Benchmark("VSTIBench", "VSTI", "vstibench-official-5subtask-v1", {
        "camera_displacement": "Cam.Disp", "camera_movement_direction": "Cam.Dir",
        "camera_obj_abs_dist": "Cam.AbsD", "camera_obj_rel_dist_v1": "Cam.RelD1",
        "camera_obj_rel_dist_v2": "Cam.RelD2", "camera_obj_rel_dist_v3": "Cam.RelD3",
        "obj_obj_relative_pos_lr": "Pos-LR", "obj_obj_relative_pos_nf": "Pos-NF",
        "obj_obj_relative_pos_ud": "Pos-UD",
    }, (("camera_obj_rel_dist_v1", "camera_obj_rel_dist_v2", "camera_obj_rel_dist_v3"),
        ("obj_obj_relative_pos_lr", "obj_obj_relative_pos_nf", "obj_obj_relative_pos_ud"))),
}
STUDENTS = {"onethinker_8b": "OneThinker-8B", "qwen35_9b": "Qwen3.5-9B", "qwen36_27b": "Qwen3.6-27B"}
CONDITIONS = {"base": "Base", "orchard_base": "Base (Orchard)", "orchard_base_b16": "Base (Orchard, batched)",
              "answer_only": "Answer-only control", "answer_only_corrected": "Answer-only (corrected set)",
              "armc": "Arm C", "setb_pilot": "Set B pilot", "setb_pilot_b16": "Set B pilot (batched)",
              "full_scale": "Full-scale", "trace_corrected": "Trace student (corrected set)",
              "r6_formatA": "r6 (format-A)", "base_27b_thinkoff": "Base (thinking off)",
              "base_27b_pinned": "Base (pinned thinking)", "base_27b_b8": "Base (batched bs8)",
              "armc_27b_b8": "Arm C student (batched bs8)"}
ORDER = {"base": 0, "orchard_base": 0, "orchard_base_b16": 0, "answer_only": 1,
         "answer_only_corrected": 1, "armc": 2, "setb_pilot": 3, "setb_pilot_b16": 3,
         "full_scale": 4, "trace_corrected": 4, "r6_formatA": 5, "base_27b_thinkoff": 6,
         "base_27b_pinned": 6, "base_27b_b8": 6, "armc_27b_b8": 7}
TOLERANCE = 0.005
HARNESSES = {"trinity-58794b8": "58794b8", "orchard-12e477b": "12e477b",
             "orchard-12e477b-b16": "12e477b", "orchard-0ab73f9-b8": "0ab73f9"}
BASE_CONDITIONS = {"base", "orchard_base", "orchard_base_b16", "base_27b_thinkoff", "base_27b_pinned", "base_27b_b8"}
TABLES = {"main", "appendix", "omit"}
MAIN_TABLE_CAPTION = ("The corrected training set contains 7,684 room-fixed rows, and lenient accuracy is the primary metric. "
                      "Qwen3.5-9B rows use batched bs16 decoding and pair only with the batched base.")


class ScoreError(ValueError):
    pass


class QuantityUnavailable(ValueError):
    pass


def canonical_mean(values):
    values = [Decimal(str(value)) for value in values]
    if not values or not all(value.is_finite() for value in values):
        raise ScoreError("Cannot average empty or nonfinite scores")
    with localcontext() as context:
        context.prec = 50
        return float((sum(values) / len(values)).quantize(Decimal("1e-15"), rounding=ROUND_HALF_EVEN))


def official_score(categories, benchmark):
    spec = BENCHMARKS[benchmark]
    if set(categories) != set(spec.categories):
        raise ScoreError(f"{benchmark}: category membership differs: {set(categories) ^ set(spec.categories)}")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
           or not 0 <= value <= 1 for value in categories.values()):
        raise ScoreError(f"{benchmark}: category scores must be finite fractions in [0, 1]")
    collapsed = {name for group in spec.groups for name in group}
    tasks = [canonical_mean(categories[name] for name in group) for group in spec.groups]
    tasks.extend(categories[name] for name in spec.categories if name not in collapsed)
    return canonical_mean(tasks)


@dataclass
class Metrics:
    categories: dict[str, float]
    overall: float
    macro: float
    counts: dict[str, int]
    failures: dict[str, int] | None
    qids: dict[str, str]

    @property
    def parse_failures(self):
        return None if self.failures is None else sum(self.failures.values())


def recompute(rows, benchmark, credit_field="credit", answer_field="parsed_answer"):
    values, counts, failures, qids = defaultdict(list), Counter(), Counter(), {}
    have_answers = all(answer_field in row for row in rows)
    for row in rows:
        qid, category = str(row["qid"]), row["category"]
        if qid in qids:
            raise ScoreError(f"Duplicate question ID: {qid}")
        credit = row[credit_field]
        if isinstance(credit, bool) or not isinstance(credit, (int, float)) or not math.isfinite(credit) or not 0 <= credit <= 1:
            raise ScoreError(f"{qid}: invalid {credit_field}: {credit!r}")
        qids[qid] = category
        values[category].append(credit)
        counts[category] += 1
        if have_answers:
            failures[category] += row[answer_field] is None or row[answer_field] == ""
    categories = {name: canonical_mean(credits) for name, credits in values.items()}
    return Metrics(categories, official_score(categories, benchmark), canonical_mean(categories.values()),
                   dict(counts), dict(failures) if have_answers else None, qids)


def assert_score(actual, stored, context):
    if not isinstance(stored, (int, float)) or not math.isfinite(stored):
        raise ScoreError(f"{context}: stored score is not finite: {stored!r}")
    if abs(round(actual * 100, 2) - round(stored * 100, 2)) > TOLERANCE + 1e-10:
        raise ScoreError(f"{context}: computed {actual * 100:.2f} != stored {stored * 100:.2f}")


def verify_summary(metrics, stored, context):
    if set(metrics.categories) != set(stored["category_scores"]):
        raise ScoreError(f"{context}: stored category membership differs")
    for name, value in metrics.categories.items():
        assert_score(value, stored["category_scores"][name], f"{context}/{name}")
    assert_score(metrics.overall, stored["primary_score"], f"{context}/primary_score")
    assert_score(metrics.macro, stored["raw_category_macro"], f"{context}/raw_category_macro")
    if metrics.parse_failures is not None and metrics.parse_failures != stored["parse_failures"]:
        raise ScoreError(f"{context}/parse_failures: computed {metrics.parse_failures} != stored {stored['parse_failures']}")


def read_json(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


@dataclass
class Cell:
    entry: dict
    strict: Metrics | None = None
    lenient: Metrics | None = None
    recorded: dict = field(default_factory=dict)
    sources: tuple[Path, ...] = ()
    lenient_recomputed: bool = False
    median_tokens: float | None = None
    strict_rows: tuple[dict, ...] = ()
    lenient_rows: tuple[dict, ...] = ()
    empty_qids: frozenset[str] = frozenset()

    @property
    def provisional(self):
        return self.entry.get("provisional", False)

    @property
    def identity(self):
        return "/".join(str(self.entry[key]) for key in ("student", "benchmark", "condition", "seed"))

    @property
    def complete(self):
        return self.entry["status"] == "complete"

    @property
    def reference(self):
        return self.entry.get("reference_only", False) or self.entry["condition"] in {"r6_formatA", "base_27b_thinkoff"}

    @property
    def label(self):
        return self.entry.get("label", CONDITIONS.get(self.entry["condition"], self.entry["condition"]))


def load_cell(entry, base_dir=None):
    entry = dict(entry)
    required = {"student", "benchmark", "condition", "seed", "strict_score_path", "lenient_score_path",
                "lenient_cell_key", "harness_commit", "harness", "base_ref", "status", "provenance_note", "protocol"}
    if required - entry.keys():
        raise ScoreError(f"Manifest cell lacks {sorted(required - entry.keys())}")
    if entry["student"] not in STUDENTS or entry["benchmark"] not in BENCHMARKS:
        raise ScoreError(f"Unknown student or benchmark: {entry}")
    if entry["seed"] not in (17, "rep2", "rep3"):
        raise ScoreError(f"Unknown published/replicate identifier: {entry['seed']!r}")
    harness = entry["harness"]
    if harness not in HARNESSES or not str(entry["harness_commit"]).startswith(HARNESSES[harness]):
        raise ScoreError(f"Invalid harness or harness commit: {harness!r}, {entry['harness_commit']!r}")
    if entry["protocol"] in {"trinity", "orchard"} and not harness.startswith(entry["protocol"] + "-"):
        raise ScoreError("The comparison protocol differs from its harness")
    if entry["base_ref"] not in BASE_CONDITIONS:
        raise ScoreError(f"Invalid base_ref: {entry['base_ref']!r}")
    if "table" in entry and entry["table"] not in TABLES:
        raise ScoreError(f"Invalid table placement: {entry['table']!r}")
    entry.setdefault("table", "main")
    entry.setdefault("provisional", False)
    entry.setdefault("empty_items", 0)
    entry.setdefault("empty_statuses", [])
    entry.setdefault("main_matched", False)
    if (type(entry["provisional"]) is not bool or type(entry["empty_items"]) is not int or entry["empty_items"] < 0
            or type(entry["main_matched"]) is not bool):
        raise ScoreError("Invalid provisional flag, empty_items count, or main_matched flag")
    statuses = entry["empty_statuses"]
    if (not isinstance(statuses, list) or any(not isinstance(status, str) or not status or status == "ok" for status in statuses)
            or len(statuses) != len(set(statuses))):
        raise ScoreError("empty_statuses must name distinct non-ok score statuses")
    if entry["empty_items"] and (not entry["provisional"] or not statuses or entry["status"] != "complete"):
        raise ScoreError("Empty items require a complete, provisional cell and audited empty_statuses")
    if entry["main_matched"] and (entry["table"] != "main" or not entry["empty_items"]):
        raise ScoreError("A main matched row requires a main-table audited empty-item set")
    cell = Cell(entry)
    paths = ("strict_score_path", "lenient_score_path", "lenient_cell_key")
    if not cell.complete:
        if entry["status"] != "pending" or any(entry[key] is not None for key in paths):
            raise ScoreError(f"{cell.identity}: pending cells require null paths and key")
        return cell
    if not all(entry[key] for key in (*paths, "harness_commit")):
        raise ScoreError(f"{cell.identity}: complete cells require score paths, key, and harness commit")
    base_dir = Path(base_dir or Path.cwd())
    for key in ("strict_score_path", "lenient_score_path", "lenient_per_question_path"):
        if entry.get(key):
            entry[key] = str((base_dir / entry[key]).resolve())
    strict_dir = Path(entry["strict_score_path"])
    score_path, item_path = strict_dir / "scores.json", strict_dir / "per_question_scores.jsonl"
    recorded = read_json(score_path)
    raw = item_path.read_bytes()
    pin = recorded.get("per_question_scores", {})
    if "sha256" in pin and hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ScoreError(f"{cell.identity}: strict per-question sha256 mismatch")
    if "size_bytes" in pin and len(raw) != pin["size_bytes"]:
        raise ScoreError(f"{cell.identity}: strict per-question byte count mismatch")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    benchmark = entry["benchmark"]
    expected = recorded["expected_count"]
    if (recorded["benchmark"] != benchmark or recorded["metric"] != BENCHMARKS[benchmark].metric
            or not recorded["coverage_complete"] or not recorded["official_aggregation_complete"]
            or recorded["terminal_count"] != expected or len(rows) != expected or recorded["missing_count"] != 0):
        raise ScoreError(f"{cell.identity}: benchmark, metric, or complete coverage contract differs")
    cell.strict_rows = tuple(rows)
    cell.strict = recompute(rows, benchmark)
    verify_summary(cell.strict, recorded, f"{cell.identity}/scores.json")
    empty_rows = [row for row in rows if row.get("status") in statuses]
    cell.empty_qids = frozenset(str(row["qid"]) for row in empty_rows)
    if len(empty_rows) != entry["empty_items"]:
        raise ScoreError(f"{cell.identity}: empty_items differs from the audited score statuses")
    if statuses and (any("status" not in row for row in rows)
                     or any(sum(row["status"] == status for row in rows) != recorded["failure_counts"].get(status, 0)
                            for status in statuses)):
        raise ScoreError(f"{cell.identity}: empty status counts differ from scores.json")
    if any(row["credit"] != 0 or row["parsed_answer"] not in (None, "") for row in empty_rows):
        raise ScoreError(f"{cell.identity}: audited empty items have answers or nonzero credits")
    cell.recorded = recorded
    lenient_path = Path(entry["lenient_score_path"])
    rescore = read_json(lenient_path)["cells"][entry["lenient_cell_key"]]
    if rescore["benchmark"] != benchmark or rescore["metric"] != recorded["metric"] or rescore["items"] != expected:
        raise ScoreError(f"{cell.identity}: lenient rescore identity/coverage differs")
    if Path(rescore["scores_dir"]).resolve() != strict_dir:
        raise ScoreError(f"{cell.identity}: lenient rescore names a different strict score directory")
    verify_summary(cell.strict, rescore["strict"], f"{cell.identity}/lenient_scores.json/strict")
    lenient_items = Path(entry.get("lenient_per_question_path") or
                         lenient_path.with_name(f"per_question_{entry['lenient_cell_key']}.jsonl"))
    cell.sources = (score_path, item_path, lenient_path)
    if lenient_items.is_file() or entry.get("lenient_per_question_path"):
        paired = read_jsonl(lenient_items)
        strict_replay = recompute(paired, benchmark, "strict_credit", "strict_answer")
        if strict_replay.qids != cell.strict.qids:
            raise ScoreError(f"{cell.identity}: lenient per-question membership differs")
        strict_index = {str(row["qid"]): row for row in rows}
        for row in paired:
            original = strict_index[str(row["qid"])]
            if abs(row["strict_credit"] - original["credit"]) > 1e-12 or row["strict_answer"] != original["parsed_answer"]:
                raise ScoreError(f"{cell.identity}/{row['qid']}: strict replay differs from per-question score")
        cell.lenient_rows = tuple(paired)
        cell.lenient = recompute(paired, benchmark, "lenient_credit", "lenient_answer")
        if any(row["lenient_credit"] != 0 or row["lenient_answer"] not in (None, "")
               for row in paired if str(row["qid"]) in cell.empty_qids):
            raise ScoreError(f"{cell.identity}: lenient scores recover audited empty items")
        cell.sources += (lenient_items,)
        cell.lenient_recomputed = True
    else:
        stored = rescore["lenient"]
        categories = stored["category_scores"]
        cell.lenient = Metrics(categories, official_score(categories, benchmark), canonical_mean(categories.values()),
                               cell.strict.counts, None, cell.strict.qids)
    verify_summary(cell.lenient, rescore["lenient"], f"{cell.identity}/lenient_scores.json/lenient")
    cell.recorded = {**recorded, "lenient_parse_failures": rescore["lenient"]["parse_failures"]}
    for key in ("expected_count", "terminal_count", "parse_failures", "lenient_parse_failures", "cap_count", "cap_without_answer_count"):
        value = cell.recorded[key]
        if type(value) is not int or not 0 <= value <= expected:
            raise ScoreError(f"{cell.identity}: invalid count {key}={value!r}")
    if not 0 <= recorded["cap_without_answer_count"] <= recorded["cap_count"] <= expected:
        raise ScoreError(f"{cell.identity}: invalid generation-cap counts")
    cell.median_tokens = recorded.get("median_gen_tokens")
    if all("generated_tokens" in row for row in rows):
        cell.median_tokens = statistics.median(row["generated_tokens"] for row in rows)
    return cell


def paired_base(cell, cells):
    matches = [base for base in cells if base.entry["student"] == cell.entry["student"]
               and base.entry["benchmark"] == cell.entry["benchmark"]
               and base.entry["condition"] == cell.entry["base_ref"] and base.entry["seed"] == 17]
    if len(matches) != 1:
        raise ScoreError(f"{cell.identity}: base_ref resolves to {len(matches)} bases")
    base = matches[0]
    if base.entry["harness"] != cell.entry["harness"]:
        raise ScoreError(f"{cell.identity}: base_ref crosses harnesses")
    if not cell.reference and (base.reference or base.entry["protocol"] != cell.entry["protocol"]):
        raise ScoreError(f"{cell.identity}: base_ref crosses comparison protocols")
    if cell.entry["condition"] in BASE_CONDITIONS and base is not cell:
        raise ScoreError(f"{cell.identity}: a base must reference itself")
    if cell.complete and not base.complete:
        raise ScoreError(f"{cell.identity}: a complete cell requires a complete paired base")
    return base


def load_manifest(path):
    path = Path(path).resolve()
    manifest = read_json(path)
    if manifest.get("schema") != "split-paper-tables-v1":
        raise ScoreError("Unknown paper-table manifest schema")
    cells = [load_cell(entry, path.parent) for entry in manifest["cells"]]
    identities = [cell.identity for cell in cells]
    if len(set(identities)) != len(identities):
        raise ScoreError("Duplicate manifest cell identity")
    cohorts = {}
    for cell in cells:
        paired_base(cell, cells)
        if cell.complete:
            benchmark = cell.entry["benchmark"]
            if benchmark in cohorts and cell.strict.qids != cohorts[benchmark]:
                raise ScoreError(f"{cell.identity}: question membership differs across benchmark cells")
            cohorts[benchmark] = cell.strict.qids
    return cells


def seed_summary(cells, mode="lenient", category=None, *, excluded=()):
    scopes = {tuple(cell.entry[key] for key in ("student", "benchmark", "condition", "harness", "protocol", "base_ref"))
              for cell in cells}
    if len(scopes) > 1:
        raise ScoreError("A seed summary cannot mix harnesses or comparison cohorts")
    seeds = [cell.entry["seed"] for cell in cells]
    if len(seeds) != len(set(seeds)):
        raise ScoreError("A seed summary cannot contain duplicate run identifiers")
    values = {}
    for cell in cells:
        if cell.complete:
            values[str(cell.entry["seed"])] = raw_quantity(cell, "score", mode, category, excluded=excluded) * 100
    data = list(values.values())
    return {"published": values.get("17"), "rep2": values.get("rep2"), "rep3": values.get("rep3"),
            "mean": statistics.mean(data) if data else None,
            "range": max(data) - min(data) if data else None,
            "sample_std": statistics.stdev(data) if len(data) > 1 else None,
            "n": len(data), "planned": len(cells)}


@dataclass
class Mismatch:
    cell: str
    quantity: str
    doc_value: str
    computed: float | None
    cause: str
    line: int


@dataclass
class CheckReport:
    checked: int = 0
    issues: list[Mismatch] = field(default_factory=list)

    def compare(self, cell, quantity, doc_value, getter, line):
        self.checked += 1
        try:
            computed = getter()
            if computed is None:
                raise QuantityUnavailable("The score artifacts do not contain this quantity")
            if not math.isfinite(computed):
                raise QuantityUnavailable("The computed quantity is not finite")
            if abs(round(computed, 2) - round(float(doc_value), 2)) <= TOLERANCE + 1e-10:
                return
            cause = "Unrounded score-derived calculation differs after rounding to two decimals"
        except (QuantityUnavailable, KeyError) as exc:
            computed, cause = None, str(exc)
        self.issues.append(Mismatch(cell, quantity, str(doc_value), computed, cause, line))

    def format_text(self):
        lines = [f"Checked {self.checked} numeric quantities: {self.checked - len(self.issues)} reproduced, "
                 f"{len(self.issues)} mismatches/unavailable."]
        for item in self.issues:
            value = "unavailable" if item.computed is None else f"{item.computed:.2f} (raw {item.computed:.15g})"
            lines.append(f"line {item.line} | {item.cell} | {item.quantity} | doc={item.doc_value} | "
                         f"computed={value} | {item.cause}")
        return "\n".join(lines) + "\n"

    def format_markdown(self):
        lines = ["# Document reproduction mismatches", "", self.format_text().splitlines()[0], "",
                 "The checker reads score artifacts only and leaves the document unchanged.", "",
                 "| Document line | Cell | Quantity | Document | Computed | Cause |",
                 "|---:|---|---|---:|---:|---|"]
        for item in self.issues:
            value = "unavailable" if item.computed is None else f"{item.computed:.2f} (raw {item.computed:.15g})"
            values = [str(item.line), item.cell, item.quantity, item.doc_value, value, item.cause]
            lines.append("| " + " | ".join(text.replace("|", "\\|").replace("\n", " ") for text in values) + " |")
        if not self.issues:
            lines.append("\nEvery covered numeric quantity reproduced.")
        return "\n".join(lines) + "\n"


def clean_doc(value):
    return value.replace("**", "").replace("`", "").replace("−", "-").strip().rstrip("*").strip()


def numeric_parts(value):
    value = re.sub(r"\s*\((?:lenient|strict)\)", "", clean_doc(value), flags=re.IGNORECASE)
    parts = re.split(r"\s*(?:→|->|/)\s*", value)
    return parts if parts and all(re.fullmatch(r"[+-]?\d+(?:\.\d+)?", part) for part in parts) else []


def document_tables(text):
    headings, lines, index = {}, text.splitlines(), 0
    while index < len(lines):
        match = re.match(r"^(#{1,6})\s+(.+)", lines[index])
        if match:
            level = len(match[1])
            headings = {key: value for key, value in headings.items() if key < level}
            headings[level] = match[2]
        if (lines[index].startswith("|") and index + 1 < len(lines)
                and re.fullmatch(r"[| :\-]+", lines[index + 1])):
            header = [clean_doc(value) for value in lines[index].strip().strip("|").split("|")]
            index += 2
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append((index + 1, [clean_doc(value) for value in lines[index].strip().strip("|").split("|")]))
                index += 1
            yield dict(headings), header, rows
            continue
        index += 1


def benchmark_from_text(text):
    return next((key for key, spec in BENCHMARKS.items() if spec.name.lower() in text.lower()), None)


def aliases(cell):
    entry = cell.entry
    if entry["seed"] in ("rep2", "rep3"):
        defaults = [entry["seed"], f"replicate {entry['seed'][-1]}"]
        if entry["protocol"] == "trinity" and entry["condition"] == "armc":
            defaults.append(f"trinity arm C (replicate {entry['seed'][-1]})")
    else:
        defaults = {"base": ["base", "trinity base"],
                    "armc": ["arm C", "arm C (published)", "published", "trinity arm C (published)"],
                    "answer_only": ["answer-only", "trinity answer-only"], "r6_formatA": ["r6", "run r6"],
                    "orchard_base": ["Orchard base", "Orchard base (PROVISIONAL)"],
                    "setb_pilot": ["Set B distilled (Orchard)"],
                    "base_27b_thinkoff": ["qwen36_27b_base_vsi_thinkoff"],
                    "base_27b_b8": ["Base"], "armc_27b_b8": ["Arm C student"]}.get(entry["condition"], [])
    return {clean_doc(value).lower() for value in defaults + entry.get("doc_aliases", [])}


def find_cell(cells, student, benchmark, label):
    matches = [cell for cell in cells if cell.entry["student"] == student
               and cell.entry["benchmark"] == benchmark and clean_doc(label).lower() in aliases(cell)]
    if len(matches) != 1:
        raise QuantityUnavailable(f"Manifest resolves {label!r} to {len(matches)} cells")
    return matches[0]


def score_view(cell, mode, excluded=()):
    if not cell.complete:
        raise QuantityUnavailable("Manifest cell is pending")
    if not excluded:
        return getattr(cell, mode)
    if not set(excluded) <= cell.strict.qids.keys():
        raise QuantityUnavailable("Excluded qids are outside the cell's score membership")
    rows = cell.strict_rows if mode == "strict" else cell.lenient_rows
    if not rows:
        raise QuantityUnavailable(f"{mode.title()} per-question scores are unavailable for a matched subset")
    selected = [row for row in rows if str(row["qid"]) not in excluded]
    fields = ("credit", "parsed_answer") if mode == "strict" else ("lenient_credit", "lenient_answer")
    return recompute(selected, cell.entry["benchmark"], *fields)


def raw_quantity(cell, quantity, mode="strict", category=None, *, excluded=(), excluded_category=None):
    metrics = score_view(cell, mode, excluded)
    if quantity == "score":
        return metrics.overall if category is None else metrics.categories[category]
    if quantity == "macro":
        if excluded_category is not None:
            if excluded_category not in metrics.categories:
                raise QuantityUnavailable(f"Unknown excluded category: {excluded_category}")
            return canonical_mean(value for name, value in metrics.categories.items() if name != excluded_category)
        return metrics.macro
    if quantity == "n":
        return metrics.counts[category] if category else len(metrics.qids)
    if quantity == "parse":
        if category or excluded:
            if metrics.failures is None:
                raise QuantityUnavailable("Lenient per-question answers are unavailable")
            return metrics.failures[category] if category else metrics.parse_failures
        return cell.recorded["parse_failures" if mode == "strict" else "lenient_parse_failures"]
    if excluded:
        raise QuantityUnavailable(f"Matched-subset {quantity} is unavailable from the score artifacts")
    if quantity == "median":
        if cell.median_tokens is None:
            raise QuantityUnavailable("Token medians require generation-token data absent from scores.json and per-question score files")
        return cell.median_tokens
    if quantity == "interrupted":
        return cell.recorded["failure_counts"].get("interrupted", 0)
    keys = {"cap": "cap_count", "cap_without": "cap_without_answer_count", "terminal": "terminal_count"}
    if quantity in keys:
        return cell.recorded[keys[quantity]]
    raise QuantityUnavailable(f"Unsupported quantity: {quantity}")


def matched_excluded_qids(base, cell):
    return base.empty_qids or cell.empty_qids


def describe_quantity(text):
    text = text.lower()
    mode = "lenient" if "lenient" in text else "strict"
    if "macro" in text:
        return "macro", mode, 100
    if "primary score" in text:
        return "score", mode, 100
    if "parse fail" in text:
        return "parse", mode, 1
    if "interrupt" in text:
        return "interrupted", mode, 1
    if "no answer" in text or "without answer" in text or "w/o answer" in text:
        return "cap_without", mode, 1
    if "cap" in text:
        return "cap", mode, 1
    raise QuantityUnavailable(f"Unsupported quantity: {text}")


def column_label(text):
    return re.sub(r"\s+(?:lenient|strict|parse fail).*", "", text, flags=re.IGNORECASE).strip()


def check_document(path, cells):
    report = CheckReport()
    model_lookup = {value.lower(): key for key, value in STUDENTS.items()}
    for headings, header, rows in document_tables(Path(path).read_text(encoding="utf-8")):
        student = model_lookup.get(clean_doc(headings.get(2, "")).lower())
        if student is None or not any(cell.entry["student"] == student for cell in cells):
            continue
        benchmark = benchmark_from_text(headings.get(3, ""))
        orchard = "orchard" in headings.get(3, "").lower()
        strict_context = "strict parser" in headings.get(4, "").lower()
        matched_context = "matched" in headings.get(4, "").lower()
        table_kind = header[0].lower()
        for line, row in rows:
            if len(row) != len(header):
                raise ScoreError(f"Document line {line}: table row has {len(row)} cells, expected {len(header)}")
            row_benchmark = benchmark_from_text(row[0]) if table_kind == "benchmark" else benchmark
            scope = [cell for cell in cells if cell.entry["student"] == student and cell.entry["benchmark"] == row_benchmark]
            if row_benchmark is None or not scope:
                continue
            excluded_category = next((category for category in BENCHMARKS[row_benchmark].categories
                                      if re.search(rf"\bexcl\.\s+{re.escape(category)}\b", row[0], flags=re.IGNORECASE)),
                                     None)
            group = [cell for cell in scope if cell.entry["condition"] == "armc"
                     and cell.entry["harness"] == "trinity-58794b8" and cell.entry["protocol"] == "trinity"]
            mean_row = re.fullmatch(r"trinity arm C, (\d+)-seed mean", row[0], flags=re.IGNORECASE)
            identity = f"{student}/{row_benchmark}/{row[0]}"

            def get(label):
                label = re.sub(r",\s*(?:\d+-item matched cohort.*|matched \d+/\d+.*|all \d+ lower bound|all \d+(?: \(prov\.\))?|excl\. \d+)$", "", label)
                if orchard and label.lower() in {"base", "distilled"}:
                    label = "Orchard base" if label.lower() == "base" else "Set B distilled (Orchard)"
                return find_cell(scope, student, row_benchmark, label)

            for column, text in zip(header[1:], row[1:]):
                low = column.lower()
                if table_kind == "cell" and low == "harness":
                    if not text:
                        continue
                    try:
                        cell = get("arm C" if mean_row else row[0])
                        expected = {cell.entry["harness"], cell.entry["harness_commit"], HARNESSES[cell.entry["harness"]]}
                        if cell.entry["harness"] == "orchard-12e477b":
                            expected.add("orchard_trainer_12e477b")
                        if text not in expected:
                            raise QuantityUnavailable(f"Document harness {text!r} differs from {cell.entry['harness']}")
                    except QuantityUnavailable as exc:
                        report.checked += 1
                        report.issues.append(Mismatch(identity, column, text, None, str(exc), line))
                    continue
                parts = numeric_parts(text)
                if not parts:
                    if clean_doc(text) not in ("--", "-", "", "pending", "—"):
                        report.compare(identity, column, text, lambda: unavailable("Unrecognized numeric cell format"), line)
                    continue
                modes = re.findall(r"\((lenient|strict)\)", text, flags=re.IGNORECASE)
                for part_index, doc_value in enumerate(parts):
                    quantity_name = f"{column} [{part_index + 1}]" if len(parts) > 1 else column
                    calculation = {}

                    def compute():
                        if modes and len(modes) != len(parts):
                            raise QuantityUnavailable("Parser labels do not cover every numeric component")
                        mode = modes[part_index].lower() if modes else "lenient" if "lenient" in low else "strict"
                        excluded = frozenset()
                        matched_label = column if table_kind == "question type" else row[0]
                        if (not re.search(r"\ball \d+\b", matched_label, flags=re.IGNORECASE)
                                and (matched_context or "matched cohort" in row[0].lower()
                                or re.search(r"\bmatched \d+/\d+", row[0].lower()) or "excl." in low)):
                            cell = get(column_label(column) if table_kind == "question type" else row[0])
                            base = paired_base(cell, cells)
                            excluded = matched_excluded_qids(base, cell)
                            if not excluded and cell is base:
                                candidates = [candidate for candidate in scope if candidate.complete
                                              and candidate.entry.get("main_matched")
                                              and paired_base(candidate, cells) is base]
                                if len(candidates) == 1:
                                    excluded = matched_excluded_qids(base, candidates[0])
                            if not excluded:
                                raise QuantityUnavailable("Matched scope lacks audited empty-item qids in score files")
                            count = re.search(r"(?:(\d+)-item matched cohort|matched (\d+)/(\d+))", row[0])
                            if count and int(count[1] or count[2]) != len(base.strict.qids) - len(excluded):
                                raise QuantityUnavailable("The document's matched cohort size differs from score membership")
                        if table_kind == "benchmark":
                            summary = seed_summary(group)
                            names = {"published": "published", "replicate 2": "rep2", "replicate 3": "rep3",
                                     "mean": "mean", "range (max-min)": "range", "sample std": "sample_std"}
                            return summary[names[low]]
                        if table_kind == "cell":
                            if mean_row:
                                summary = seed_summary(group, mode)
                                if int(mean_row[1]) != summary["n"] or not ("lenient" in low or "strict" in low):
                                    raise QuantityUnavailable("The repeated-run mean row has an unsupported quantity or run count")
                                return summary["mean"]
                            cell = get(row[0])
                            if "macro" in low:
                                quantity, scale = "macro", 100
                            elif "parse fail" in low:
                                quantity, scale = "parse", 1
                                mode = "strict" if part_index == 0 else "lenient"
                            elif "lenient" in low or "strict" in low:
                                quantity, scale = "score", 100
                            elif low == "terminal":
                                quantity, scale = ("terminal" if part_index == 0 else "n"), 1
                            elif "median" in low:
                                quantity, scale = "median", 1
                            else:
                                quantity, mode, scale = describe_quantity(low)
                            if excluded and quantity == "score":
                                score_rows = cell.strict_rows if mode == "strict" else cell.lenient_rows
                                credit = "credit" if mode == "strict" else "lenient_credit"
                                if score_rows:
                                    calculation["flat"] = statistics.mean(item[credit] for item in score_rows
                                                                           if str(item["qid"]) not in excluded) * 100
                            return raw_quantity(cell, quantity, mode, excluded=excluded,
                                                excluded_category=excluded_category) * scale
                        category = row[0] if table_kind == "question type" and "macro" not in row[0].lower() else None
                        if table_kind == "question type":
                            if low == "n":
                                target = next(cell for cell in scope if cell.complete)
                                return raw_quantity(target, "n", category=category, excluded=excluded)
                            if "delta" in low and not strict_context and any("lenient" in label.lower() for label in header):
                                mode = "lenient"
                            quantity = "macro" if "macro" in row[0].lower() else "parse" if "parse fail" in low else "score"
                            scale = 1 if quantity == "parse" else 100
                        elif table_kind == "quantity":
                            quantity, mode, scale = describe_quantity(row[0])
                        else:
                            raise QuantityUnavailable(f"Unsupported table header: {header[0]}")
                        if "delta" in low or " - " in low:
                            if low == "delta vs arm c":
                                raise QuantityUnavailable("cross-harness reference column")
                            expression = re.sub(r"\s*delta\s*", "", column, flags=re.IGNORECASE).strip()
                            if " - " in expression:
                                left, right = expression.split(" - ", 1)
                            else:
                                left = "Set B distilled (Orchard)" if orchard else "r6" if any("r6" in label.lower() for label in header) else "arm C"
                                right = "Orchard base" if orchard else "base"
                            left, right = get(left), get(right)
                            if left.entry["harness"] != right.entry["harness"]:
                                raise QuantityUnavailable("A cross-harness delta is not a matched comparison")
                            values = [raw_quantity(cell, quantity, mode, category, excluded=excluded,
                                                   excluded_category=excluded_category) for cell in (left, right)]
                            calculation["rounded_delta"] = round(values[0] * scale, 2) - round(values[1] * scale, 2)
                            return (values[0] - values[1]) * scale
                        return raw_quantity(get(column_label(column)), quantity, mode, category, excluded=excluded,
                                            excluded_category=excluded_category) * scale

                    previous_issues = len(report.issues)
                    report.compare(identity, quantity_name, doc_value, compute, line)
                    if len(report.issues) == previous_issues:
                        continue
                    if "flat" in calculation and abs(round(calculation["flat"], 2) - float(doc_value)) <= TOLERANCE + 1e-10:
                        report.issues[-1].cause = (
                            "The document matches a flat per-question mean on the matched subset; "
                            f"the generator retains {BENCHMARKS[row_benchmark].metric} category collapse")
                    elif "rounded_delta" in calculation and abs(round(calculation["rounded_delta"], 2) - float(doc_value)) <= TOLERANCE + 1e-10:
                        report.issues[-1].cause = "The document subtracts rounded scores; the generator subtracts full-precision scores before rounding"
                    if table_kind == "benchmark":
                        rounded = [round(cell.lenient.overall * 100, 2) for cell in group if cell.complete]
                        functions = {"mean": statistics.mean, "sample std": statistics.stdev,
                                     "range (max-min)": lambda values: max(values) - min(values)}
                        if len(rounded) > 1 and low in functions:
                            alternative = functions[low](rounded)
                            if abs(round(alternative, 2) - float(doc_value)) <= TOLERANCE + 1e-10:
                                report.issues[-1].cause = (
                                    f"The document matches statistics over already rounded seed scores {rounded}; "
                                    "the generator retains full score precision until the final display rounding")
    if not report.checked:
        raise ScoreError("Document check covered no numeric result quantities")
    return report


def unavailable(message):
    raise QuantityUnavailable(message)


def latex_escape(text):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(text))


def condition_groups(cells, benchmark=None, references=False):
    grouped = defaultdict(list)
    for cell in cells:
        if (benchmark is None or cell.entry["benchmark"] == benchmark) and cell.reference == references:
            grouped[(cell.entry["student"], cell.entry["protocol"], cell.entry["condition"],
                     cell.entry["benchmark"], cell.entry["harness"], cell.entry["base_ref"])].append(cell)
    students = list(STUDENTS)
    protocols = {"trinity": 0, "orchard": 1}
    keys = sorted(grouped, key=lambda key: (students.index(key[0]), protocols.get(key[1], 2), key[4],
                                           ORDER.get(key[2], 99), key[3], key[2]))
    return [sorted(grouped[key], key=lambda cell: {17: 0, "rep2": 1, "rep3": 2}[cell.entry["seed"]]) for key in keys]


def cells_for_table(cells, table):
    if table not in TABLES:
        raise ScoreError(f"Invalid table placement: {table!r}")
    placements = {"main"} if table == "main" else {"main", "appendix"}
    return [cell for cell in cells if cell.entry["table"] in placements]


def cohort(cell):
    return cell.entry["student"], cell.entry["protocol"], cell.entry["harness"]


def cohort_label(cell):
    protocol = {"trinity": "Trinity", "orchard": "Orchard",
                "formatA_reference": "format-A reference", "thinking_off_reference": "thinking-off reference"}
    return f"{STUDENTS[cell.entry['student']]} --- {protocol.get(cell.entry['protocol'], cell.entry['protocol'])}"


def row_label(cell, label=None):
    return latex_escape(cell.label if label is None else label) + (r"$^{\dagger}$" if cell.provisional else "")


def provisional_clause(cells):
    flagged = {cell.identity: cell for cell in cells if cell.complete and cell.provisional}
    if not flagged:
        return ""
    counts = "; ".join(f"{STUDENTS[cell.entry['student']]} {cell.label}: "
                       f"{len(cell.empty_qids)}/{cell.recorded['expected_count']} empty items"
                       for cell in flagged.values())
    return r" \(\dagger\) marks provisional rows (" + latex_escape(counts) + "); rows without an explicit matched label retain the full denominator."


def run_label(cell):
    return "published" if cell.entry["condition"] == "armc" and cell.entry["seed"] == 17 else str(cell.entry["seed"])


def provenance(cell):
    entry = cell.entry
    date = datetime.fromtimestamp(cell.sources[0].stat().st_mtime, timezone.utc).isoformat() if cell.sources else "pending"
    values = [f"cell={cell.identity}", f"status={entry['status']}", f"strict={entry['strict_score_path']}",
              f"lenient={entry['lenient_score_path']}#{entry['lenient_cell_key']}",
              f"harness={entry['harness']}", f"harness_commit={entry['harness_commit']}",
              f"base_ref={entry['base_ref']}", f"table={entry['table']}", f"provisional={cell.provisional}", f"empty_items={entry.get('empty_items', 0)}",
              f"scores_mtime_utc={date}",
              f"lenient_per_question_recomputed={cell.lenient_recomputed}", entry["provenance_note"]]
    return "% " + " | ".join(str(value).replace("\n", " ").replace("\r", " ") for value in values)


def number(value, *, bold=False, std=None, reserve=False, decimals=2):
    if value is None:
        return "--" + (r"\,\makebox[2.8em][l]{}" if reserve else "")
    text = f"{value:.{decimals}f}"
    if bold:
        text = r"\textbf{" + text + "}"
    if reserve or std is not None:
        suffix = "" if std is None else r"{\scriptsize$\pm$" + f"{std:.2f}" + "}"
        text += r"\,\makebox[2.8em][l]{" + suffix + "}"
    return text


def float_table(title, macro, details, label, header, rows, comments=()):
    lines = [*comments, r"\begin{table*}[t]", r"\centering",
             f"\\caption{{\\textbf{{{latex_escape(title)}}} \\{macro}{{}} {details}}}",
             r"\label{tab:" + label + "}", r"\footnotesize", r"\setlength{\tabcolsep}{3pt}",
             r"\resizebox{\linewidth}{!}{%", r"\begin{tabular}{l" + "r" * (len(header) - 1) + "}",
             r"\toprule", " & ".join(latex_escape(value) for value in header) + r" \\", r"\midrule",
             *rows, r"\bottomrule", r"\end{tabular}%", "}", r"\end{table*}", ""]
    return "\n".join(lines)


def winner_takeaway(cells, benchmark, mode):
    cohorts = defaultdict(list)
    for group in condition_groups(cells, benchmark):
        value = seed_summary(group, mode)["mean"]
        if value is not None:
            cohorts[cohort(group[0])].append((value, group[0].label))
    clauses = []
    for (student, protocol, harness), values in cohorts.items():
        if len(values) < 2:
            continue
        highest = max(value for value, _ in values)
        winners = [label for value, label in values if round(value, 2) == round(highest, 2)]
        verb = "leads" if len(winners) == 1 else "tie for the lead in"
        clauses.append(f"{' and '.join(winners)} {verb} the completed {STUDENTS[student]} {protocol.title()} conditions")
    if not clauses:
        labels = [label for values in cohorts.values() for _, label in values]
        return latex_escape(f"Only {labels[0]} has a complete result." if labels else "The planned comparisons are awaiting complete scores.")
    return latex_escape("; ".join(clauses) + ".")


def render_accuracy(cells, benchmark, mode, *, references=False, seeds=False, matched_primary=False):
    spec = BENCHMARKS[benchmark]
    groups = condition_groups(cells, benchmark, references)
    if seeds:
        groups = [[cell] for group in groups if group[0].entry["condition"] == "armc" for cell in group]
    quantities = [*spec.categories, None]
    show_base = not references and not seeds
    exclusions = [matched_excluded_qids(paired_base(group[0], cells), group[0])
                  if matched_primary and group[0].entry.get("main_matched") else frozenset()
                  for group in groups]
    summaries = [[seed_summary(group, mode, category, excluded=excluded) for category in quantities]
                 for group, excluded in zip(groups, exclusions)]
    complete_groups = Counter(cohort(group[0]) for group, values in zip(groups, summaries) if values[-1]["mean"] is not None)
    best = {}
    if not references and not seeds:
        for group, values in zip(groups, summaries):
            for index, summary in enumerate(values):
                if summary["mean"] is not None:
                    key = cohort(group[0]), index
                    best[key] = max(best.get(key, -1), summary["mean"])
    rows, previous = [], None
    for group, values, excluded in zip(groups, summaries, exclusions):
        first = group[0]
        if cohort(first) != previous:
            if previous is not None:
                rows.append(r"\midrule")
            rows.append(r"\multicolumn{" + str(len(quantities) + 1 + show_base) + r"}{l}{\textit{" + latex_escape(cohort_label(first)) + r"}} \\")
            previous = cohort(first)
        label = first.label
        if excluded:
            label += f", matched {raw_quantity(first, 'n', excluded=excluded)}/{first.recorded['expected_count']}"
        elif first.entry.get("main_matched") and not matched_primary:
            label += f", all {first.recorded['expected_count']} lower bound"
        if seeds:
            label += f" ({run_label(first)})"
        elif len(group) > 1:
            label += f" ({values[-1]['n']}/{len(group)} runs)"
        rendered = []
        for index, summary in enumerate(values):
            value = summary["mean"]
            marked = (not references and not seeds and value is not None and complete_groups[cohort(first)] > 1
                      and round(value, 2) == round(best[cohort(first), index], 2))
            rendered.append(number(value, bold=marked, std=summary["sample_std"], reserve=not seeds and not references))
        if show_base:
            base = paired_base(first, cells)
            value = raw_quantity(base, "score", mode, excluded=excluded) * 100 if base.complete else None
            rendered.insert(0, number(value) + (r"$^{\dagger}$" if base.provisional else ""))
        rows.extend(provenance(cell) for cell in group)
        rows.append(" & ".join([row_label(first, label), *rendered]) + r" \\")
    suffix = "References" + mode.title() if references else "Seeds" + mode.title() if seeds else "" if mode == "lenient" else "Strict"
    title = f"{spec.name} {'reference configurations' if references else 'individual arm-C runs' if seeds else 'question-type results'} ({mode})."
    details = r"Accuracy is in percent; Overall uses the official metric rather than the raw-category macro. "
    if references:
        reasons = {"r6_formatA": "r6 uses format-A targets", "base_27b_thinkoff": "the 27B base uses thinking off"}
        present = {group[0].entry["condition"] for group in groups}
        reasons = "; ".join(reason for condition, reason in reasons.items() if condition in present)
        details += "These configurations are not protocol-comparable with the main rows"
        details += (": " + reasons + ". " if reasons else ". ") + "No best or second-best marks apply."
    elif seeds:
        details += "Published and replicate identifiers follow the score manifest."
    else:
        details += ("Bold marks the best value within each student's matched cohort when at least two conditions are complete. "
                    "Run counts show completed/planned repeats; suffixes give sample standard deviations. "
                    "Base gives the paired same-harness overall score under this table's parser.")
    details += provisional_clause(cell for group in groups for cell in group)
    details += " These diagnostic results remain provisional."
    comments = [f"% Metric: {spec.metric}", "% Question-type legend:",
                *(f"% {short} = {name}" for name, short in spec.labels.items())]
    return float_table(title, "captakeaway" + spec.short + suffix, details,
                       spec.short.lower() + "_" + mode + "_" + ("references" if references else "seeds" if seeds else "main"),
                       ["Condition", *(["Base"] if show_base else []), *spec.labels.values(), "Overall"], rows, comments)


def render_diagnostics(cells, benchmark):
    spec = BENCHMARKS[benchmark]
    rows, previous = [], None
    groups = condition_groups(cells, benchmark) + condition_groups(cells, benchmark, True)
    for group in groups:
        for cell in group:
            if cohort(cell) != previous:
                if previous is not None:
                    rows.append(r"\midrule")
                rows.append(r"\multicolumn{7}{l}{\textit{" + latex_escape(cohort_label(cell)) + r"}} \\")
                previous = cohort(cell)
            values = [raw_quantity(cell, name, mode) if cell.complete else None for name, mode in
                      [("parse", "strict"), ("parse", "lenient"), ("cap", "strict"), ("cap_without", "strict")]]
            terminal = f"{cell.recorded['terminal_count']}/{cell.recorded['expected_count']}" if cell.complete else "--"
            rows.extend([provenance(cell), " & ".join([row_label(cell), latex_escape(run_label(cell)),
                         *(number(value, decimals=0) for value in values), terminal]) + r" \\"])
    details = ("Counts retain the full evaluation membership. Cap-without-answer uses the recorded strict-parser answer. "
               "The r6 format-A and thinking-off 27B rows are reference configurations, not matched comparisons.")
    details += provisional_clause(cell for cell in cells if cell.entry["benchmark"] == benchmark)
    return float_table(f"{spec.name} parser and generation diagnostics.", "captakeaway" + spec.short + "Diagnostics",
                       details, spec.short.lower() + "_diagnostics",
                       ["Condition", "Run", "Strict fail", "Lenient fail", "Cap-hit", "Cap w/o answer", "Terminal"], rows)


def render_macros(cells, benchmark):
    spec = BENCHMARKS[benchmark]
    rows, previous = [], None
    for group in condition_groups(cells, benchmark) + condition_groups(cells, benchmark, True):
        for cell in group:
            if cohort(cell) != previous:
                if previous is not None:
                    rows.append(r"\midrule")
                rows.append(r"\multicolumn{6}{l}{\textit{" + latex_escape(cohort_label(cell)) + r"}} \\")
                previous = cohort(cell)
            values = [raw_quantity(cell, quantity, mode) * 100 if cell.complete else None
                      for mode in ("lenient", "strict") for quantity in ("score", "macro")]
            rows.extend([provenance(cell), " & ".join([row_label(cell), latex_escape(run_label(cell)),
                         *(number(value) for value in values)]) + r" \\"])
    details = ("The official score first collapses related question types into benchmark tasks; the raw macro weights raw types equally. "
               "All values are percentages. Reference configurations carry no comparative marks.")
    details += provisional_clause(cell for cell in cells if cell.entry["benchmark"] == benchmark)
    return float_table(f"{spec.name} official scores and raw-category macros.", "captakeaway" + spec.short + "Aggregation",
                       details, spec.short.lower() + "_aggregation",
                       ["Condition", "Run", "Lenient official", "Lenient raw macro", "Strict official", "Strict raw macro"], rows)


def matched_groups(cells, benchmark):
    grouped = {}
    for group in condition_groups(cells, benchmark):
        for cell in group:
            if not cell.complete or cell.entry["condition"] in BASE_CONDITIONS:
                continue
            base = paired_base(cell, cells)
            excluded = matched_excluded_qids(base, cell)
            if excluded:
                grouped.setdefault((base.identity, excluded), [base]).append(cell)
    return list(grouped.values())


def render_matched(cells, benchmark):
    groups = matched_groups(cells, benchmark)
    if not groups:
        return None
    spec = BENCHMARKS[benchmark]
    rows = []
    for group in groups:
        base = group[0]
        excluded = matched_excluded_qids(base, group[-1])
        if rows:
            rows.append(r"\midrule")
        rows.append(r"\multicolumn{6}{l}{\textit{" + latex_escape(cohort_label(base)) + r"}} \\")
        for cell in group:
            values = [raw_quantity(cell, quantity, mode, excluded=excluded) * 100
                      for quantity, mode in (("score", "lenient"), ("score", "strict"), ("macro", "lenient"), ("macro", "strict"))]
            count = raw_quantity(cell, "n", excluded=excluded)
            rows.extend([provenance(cell), " & ".join([row_label(cell), str(count), *(number(value) for value in values)]) + r" \\"])
    details = ("The paired base's audited empty-item qids, or the student's when the base has none, are excluded from every displayed condition. "
               "Overall retains the official category collapse; raw macros weight the surviving question types equally. "
               "This selected subset is an appendix diagnostic, not the full-cohort result.")
    details += provisional_clause(cell for group in groups for cell in group)
    return float_table(f"{spec.name} matched-subset diagnostic.", "captakeaway" + spec.short + "Matched",
                       details, spec.short.lower() + "_matched",
                       ["Condition", "Items", "Lenient overall", "Strict overall", "Lenient raw macro", "Strict raw macro"], rows)


def render_seed_summaries(cells):
    rows = []
    for group in condition_groups(cells):
        if group[0].entry["condition"] != "armc":
            continue
        summary = seed_summary(group)
        rows.extend(provenance(cell) for cell in group)
        values = [summary[key] for key in ("published", "rep2", "rep3", "mean", "range", "sample_std")]
        label = f"{STUDENTS[group[0].entry['student']]} / {BENCHMARKS[group[0].entry['benchmark']].name}"
        rows.append(" & ".join([latex_escape(label), f"{summary['n']}/{summary['planned']}",
                                *(number(value) for value in values)]) + r" \\")
    details = ("Lenient official scores determine all summaries. Means, ranges, and sample standard deviations use unrounded scores "
               "from completed runs, with the sample denominator n-1. Run identifiers preserve the published/replicate labels.")
    return float_table("Arm C repeated-run summaries.", "captakeawaySeeds", details, "seed_summaries",
                       ["Student / benchmark", "Runs", "Published", "rep2", "rep3", "Mean", "Range", "Sample std"], rows)


def caption_defaults(cells):
    macros = {}
    for benchmark, spec in BENCHMARKS.items():
        for mode in ("lenient", "strict"):
            takeaway = MAIN_TABLE_CAPTION if mode == "lenient" else winner_takeaway(cells, benchmark, mode)
            macros["captakeaway" + spec.short + ("" if mode == "lenient" else "Strict")] = takeaway
            groups = [group for group in condition_groups(cells, benchmark) if group[0].entry["condition"] == "armc"]
            ranged = [(seed_summary(group, mode)["range"], group) for group in groups if seed_summary(group, mode)["n"] > 1]
            if ranged:
                _, widest = max(ranged, key=lambda pair: pair[0])
                student = STUDENTS[widest[0].entry["student"]]
                seed_text = (f"{student} has the widest observed arm-C repeat range on {spec.name}." if len(ranged) > 1
                             else f"Only {student} has enough completed arm-C runs to estimate dispersion on {spec.name}.")
            else:
                seed_text = "The planned repeats are not yet sufficient to estimate dispersion."
            macros["captakeaway" + spec.short + "Seeds" + mode.title()] = latex_escape(seed_text)
            macros["captakeaway" + spec.short + "References" + mode.title()] = (
                "These reference configurations do not support matched comparisons with the main-table conditions.")
        matched = matched_groups(cells, benchmark)
        retained = [f"{STUDENTS[group[0].entry['student']]} retains "
                    f"{len(group[0].strict.qids) - len(matched_excluded_qids(group[0], group[-1]))}/{len(group[0].strict.qids)} matched items"
                    for group in matched]
        macros["captakeaway" + spec.short + "Matched"] = latex_escape(
            "; ".join(retained) + "." if retained else "No completed comparison requires an empty-item matched subset.")
        subset = [cell for cell in cells if cell.complete and cell.entry["benchmark"] == benchmark]
        recovered = [cell for cell in subset if raw_quantity(cell, "parse", "lenient") < raw_quantity(cell, "parse", "strict")]
        diag = "Lenient parsing recovers answers that strict parsing rejects." if recovered else "Lenient parsing recovers no additional answers in the completed cells."
        macros["captakeaway" + spec.short + "Diagnostics"] = diag if subset else "The parser diagnostics await complete scores."
        differs = any(abs(cell.lenient.overall - cell.lenient.macro) > 1e-12 for cell in subset)
        macros["captakeaway" + spec.short + "Aggregation"] = (
            "The official score differs from the raw-category macro in the completed results." if differs
            else "The available official scores equal their raw-category macros." if subset
            else "The official scores and raw-category macros await complete results.")
    summaries = [(seed_summary(group)["range"], group) for group in condition_groups(cells)
                 if group[0].entry["condition"] == "armc" and seed_summary(group)["n"] > 1]
    if summaries:
        _, group = max(summaries, key=lambda pair: pair[0])
        takeaway = (f"{STUDENTS[group[0].entry['student']]} on {BENCHMARKS[group[0].entry['benchmark']].name} "
                    "has the widest observed range among the completed repeat groups.")
    else:
        takeaway = "The planned repeats are not yet sufficient to estimate dispersion."
    macros["captakeawaySeeds"] = latex_escape(takeaway)
    return "\n".join(f"\\newcommand{{\\{name}}}{{{text}}}" for name, text in macros.items()) + "\n"


def safe_output(cells, out):
    out = Path(out).resolve()
    for cell in cells:
        for source in cell.sources:
            if out == source.parent or source.parent in out.parents:
                raise ScoreError(f"Refusing to write next to read-only score artifacts: {out}")
    return out


def write_output(path, text):
    path = Path(path)
    if path.is_symlink():
        raise ScoreError(f"Refusing to overwrite a symlink: {path}")
    path.write_text(text, encoding="utf-8")


def render_all(cells, out):
    out = safe_output(cells, out)
    out.mkdir(parents=True, exist_ok=True)
    main_cells = cells_for_table(cells, "main")
    appendix_cells = cells_for_table(cells, "appendix")
    captions, generated = out / "tables_captions.tex", out / "tables_captions.generated.tex"
    defaults = caption_defaults(appendix_cells)
    old_defaults = generated.read_text(encoding="utf-8") if generated.exists() else None
    if not captions.exists() or captions.read_text(encoding="utf-8") == old_defaults:
        write_output(captions, defaults)
    write_output(generated, defaults)
    files = {}
    for benchmark, spec in BENCHMARKS.items():
        short = spec.short.lower()
        files[f"main_{short}.tex"] = render_accuracy(main_cells, benchmark, "lenient", matched_primary=True)
        files[f"appendix_{short}_strict.tex"] = render_accuracy(appendix_cells, benchmark, "strict")
        for mode in ("lenient", "strict"):
            files[f"appendix_{short}_seeds_{mode}.tex"] = render_accuracy(appendix_cells, benchmark, mode, seeds=True)
            files[f"appendix_{short}_references_{mode}.tex"] = render_accuracy(appendix_cells, benchmark, mode, references=True)
        files[f"appendix_{short}_diagnostics.tex"] = render_diagnostics(appendix_cells, benchmark)
        files[f"appendix_{short}_aggregation.tex"] = render_macros(appendix_cells, benchmark)
        matched = render_matched(appendix_cells, benchmark)
        if matched:
            files[f"appendix_{short}_matched.tex"] = matched
    files["appendix_seed_summaries.tex"] = render_seed_summaries(appendix_cells)
    for name, content in files.items():
        write_output(out / name, content)
    inputs = [r"\input{" + name + "}\n" + r"\clearpage" for name in files]
    wrapper = "\n".join([r"\documentclass{article}", r"\usepackage[T1]{fontenc}",
                         r"\usepackage[margin=15mm]{geometry}", r"\usepackage{booktabs,graphicx}",
                         r"\input{tables_captions.tex}", r"\begin{document}", *inputs, r"\end{document}", ""])
    write_output(out / "tables_preview.tex", wrapper)
    return list(files)


def compile_preview(out):
    executable = shutil.which("pdflatex")
    if executable is None:
        return False
    out = Path(out).resolve()
    for name in ("tables_preview.pdf", "tables_preview.aux", "tables_preview.log", "tables_preview_compile.txt"):
        if (out / name).is_symlink():
            raise ScoreError(f"Refusing TeX output through a symlink: {out / name}")
    env = dict(os.environ)
    for key in ("TEXMFVAR", "TEXMFCONFIG", "TEXMFOUTPUT", "TMPDIR"):
        target = out / ("tex_cache_" + key.lower())
        if target.is_symlink():
            raise ScoreError(f"Refusing TeX cache through a symlink: {target}")
        target.mkdir(exist_ok=True)
        env[key] = str(target)
    command = [executable, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
               f"-output-directory={out}", str(out / "tables_preview.tex")]
    outputs = []
    for _ in range(2):
        result = subprocess.run(command, cwd=out, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=120)
        outputs.append(result.stdout)
        write_output(out / "tables_preview_compile.txt", "\n".join(outputs))
        if result.returncode:
            raise ScoreError(f"pdflatex failed ({result.returncode}): {result.stdout[-4000:]}")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check-doc", type=Path)
    parser.add_argument("--mismatches", type=Path)
    parser.add_argument("--compile", action="store_true")
    args = parser.parse_args(argv)
    if not args.out and not args.check_doc:
        parser.error("provide --out, --check-doc, or both")
    if args.compile and not args.out:
        parser.error("--compile requires --out")
    if args.mismatches and not args.check_doc:
        parser.error("--mismatches requires --check-doc")
    try:
        cells = load_manifest(args.manifest)
        complete = sum(cell.complete for cell in cells)
        replayed = sum(cell.lenient_recomputed for cell in cells)
        print(f"Loaded {len(cells)} cells: {complete} complete, {len(cells) - complete} pending; "
              f"recomputed {complete} strict and {replayed} lenient per-question score sets.")
        if args.out:
            files = render_all(cells, args.out)
            print(f"Rendered {len(files)} floats and a preview wrapper in {args.out.resolve()}")
            if args.compile:
                print("Compiled tables_preview.pdf" if compile_preview(args.out) else "Skipped compilation: pdflatex is not on PATH")
        if args.check_doc:
            report = check_document(args.check_doc, cells)
            print(report.format_text(), end="")
            if args.mismatches:
                target = args.mismatches.absolute()
                safe_output(cells, target.parent)
                target.parent.mkdir(parents=True, exist_ok=True)
                write_output(target, report.format_markdown())
            return int(bool(report.issues))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
