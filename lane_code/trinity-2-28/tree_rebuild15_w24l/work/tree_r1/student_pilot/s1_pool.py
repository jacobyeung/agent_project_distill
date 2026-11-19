import argparse
from collections import Counter
import copy
import gzip
import json
from pathlib import Path
import re

from . import ground_rows
from .p3_provenance import file_pin, load, pinned, sha256, source_files, write, digest
from .row_removals import Removals
from .s1_exclusions import Exclusions
from .s1_scene_census import SceneCoverageError, compare


ROOM_SETS = ("T0_room", "T1H1_room", "SCENE_room")


class Pool:
    def __init__(self, manifest, room_sets=ROOM_SETS):
        self.pin = manifest
        self.manifest = load(pinned(manifest))
        if self.manifest.get("schema") != "dose-pool-s1-manifest-v2":
            raise ValueError("Unsupported pool manifest")
        entries = self.manifest["sets"]
        self.sources = {entry["name"]: entry for entry in entries}
        if len(entries) != len(self.sources) or any(
                not re.fullmatch(r"[A-Za-z0-9_]+", name) for name in self.sources):
            raise ValueError("Pool source names differ")
        self.room_sets = tuple(room_sets)
        self.lists, self.files = {}, {}
        for name in ("dev_s1", "eval_rooms", "room_release_gate"):
            value = self.manifest["exclusions"][name]
            pin = dict(path=value["list"], sha256=value["list_sha256"])
            pairs = [tuple(line.split("\t")) for line in pinned(pin).read_text().splitlines() if line.strip()]
            if (any(len(pair) != 2 or not all(pair) or pair[0] not in self.sources for pair in pairs)
                    or len(pairs) != len(set(pairs)) or len(pairs) != value["rows"]):
                raise ValueError("Pool exclusion membership count or scope differs")
            self.lists[name], self.files[name] = set(pairs), pin
        dev, benchmark = (self.manifest["exclusions"][name] for name in ("dev_s1", "eval_rooms"))
        self.scenes = Exclusions(dict(path=dev["withhold"], sha256=dev["withhold_sha256"]),
                                 dict(path=benchmark["v2"], sha256=benchmark["v2_sha256"]))

    def deferred(self, name):
        source = self.sources[name]
        if source.get("status") != "final":
            return "source_not_final"
        if ("room" in name or "room_size_estimation" in source.get("rows_per_type", {})) and name not in self.room_sets:
            return "room_set_not_authorized"
        return None

    def reasons(self, name, row):
        if name not in self.sources or not isinstance(row.get("qid"), str) or not row["qid"]:
            raise ValueError("Unknown pool source or empty QID")
        reasons = {key for key, pairs in self.lists.items() if (name, row["qid"]) in pairs}
        matches = self.scenes.matches(row)
        reasons.update(key for key, flag in (("dev_s1", "dev"), ("eval_rooms", "benchmark")) if matches[flag])
        return reasons


def normalize_room(row, tokenizer):
    if row.get("question_type") != "room_size_estimation" or "floor height -0.00 m\n" not in row["target"]:
        return row, False
    if tokenizer is None:
        raise ValueError("Canonical room text requires the pinned source tokenizer")
    from trace_format import room_v314
    from trace_format.ground_v312 import wrap
    from generator.derivgen_v7.derivgen.ground_v313_tokens import gate_positions
    record = copy.deepcopy(row["ground_record"])
    if len(record["events"]) != 1 or record["events"][0]["call"] != room_v314.CALL:
        raise ValueError("Room normalization requires one native room call")
    old = record["events"][0]["response"]
    prefix, suffix = "<tool_response>\n", "\n</tool_response>"
    if not old.startswith(prefix) or not old.endswith(suffix):
        raise ValueError("Malformed room response envelope")
    body = room_v314.parse_response(old[len(prefix):-len(suffix)])
    new = wrap(room_v314.format_result(body))
    if old.replace("floor height -0.00 m\n", "floor height 0.00 m\n") != new or row["target"].count(old) != 1:
        raise ValueError("Room normalization changes more than negative zero")
    record["events"][0]["response"] = new
    record["suffix"] = row["target"].replace(old, new)
    record["suffix_tokens"] = len(tokenizer.encode(record["suffix"]).ids)
    if "mdg_gate_token_positions" in record:
        record["mdg_gate_token_positions"] = gate_positions(tokenizer, record["suffix"])
    normalized = {**copy.deepcopy(row), **ground_rows.pack(record, row["provenance"])}
    for key in ("answer", "gt_answer", "training_admitted", "qid", "candidate_id", "provenance"):
        if normalized[key] != row[key]:
            raise ValueError("Room normalization changes labels, membership or provenance")
    ground_rows.validate(normalized)
    return normalized, True


def implementation():
    root = Path(__file__).parent.parent
    return {str(path.relative_to(root)): sha256(path) for path in source_files([Path(__file__)])}


def source_tokenizer(pin):
    if pin is None:
        return None
    from generator.derivgen_v7.derivgen.ground_v313_tokens import tokenizer_for_rows
    return tokenizer_for_rows(str(pinned(pin)))


def validate_source_row(row, kind):
    if kind == "packed":
        ground_rows.validate(row)
    elif (row.get("question_type") != "route_planning" or row.get("head_program") is not None
          or row.get("score_nomination_allowed") is not False or not isinstance(row.get("answer"), str)
          or not row.get("target", "").startswith("<think>\n")
          or not row["target"].endswith("\n</think>\n\n"+row["answer"])
          or re.search(r"<(?:ground|depth|pose|calc3d|gap|fov)\b", row["target"])):
        raise ValueError("Direct pool source is not a diagnostic route-planning row")


def scene_expectation(pool, name, rows, source):
    memberships = {kind: {qid for source_name, qid in pool.lists[key] if source_name == name}
                   for kind, key in (("dev", "dev_s1"), ("benchmark", "eval_rooms"))}
    return dict(schema="s1-scene-census-v1", method="pinned-pool-qid-membership",
                files=pool.scenes.files, membership_files=pool.files, rows=rows, source=source,
                counts=dict(dev_matches=len(memberships["dev"]), benchmark_matches=len(memberships["benchmark"]),
                            overlap_matches=len(memberships["dev"] & memberships["benchmark"])))


def prepare(manifest, output, remove_files=(), tokenizer=None, room_sets=ROOM_SETS, *, opaque=False):
    pool = Pool(manifest, room_sets)
    output = Path(output)
    output.mkdir()
    tok = source_tokenizer(tokenizer)
    sources = {}
    for name, source in pool.sources.items():
        pool.scenes.counts(name)
        kept, seen = [], set()
        counts, types, original_types = Counter(), Counter(), Counter()
        reason = pool.deferred(name)
        record = dict(status="DEFERRED" if reason else "ELIGIBLE", reason=reason)
        removals = Removals(remove_files, stream='vqa')
        try:
            kind = "packed" if "packed" in source["files"] else "rows"
            metadata = source["files"][kind]
            pin = {key: metadata[key] for key in ("path", "sha256")}
            path = pinned(pin)
            record.update(source=pin, kind=kind, declared_rows=metadata["rows"])
            pool.scenes.expected[name] = scene_expectation(pool, name, metadata["rows"], pin)
            if metadata.get("bytes", path.stat().st_size) != path.stat().st_size:
                raise ValueError("Pool source byte count differs")
            with gzip.open(path, "rt") as stream:
                for index, line in enumerate(stream):
                    row = json.loads(line)
                    qid = row.get("qid")
                    if qid in seen:
                        raise ValueError("Duplicate QID within a pool source")
                    seen.add(qid)
                    counts["seen"] += 1
                    typ = row.get("question_type", row.get("type"))
                    original_types[typ] += 1
                    pool.scenes.keep(row, name)
                    rejected = pool.reasons(name, row)
                    counts.update(rejected)
                    listed = {key for key, pairs in pool.lists.items() if (name, qid) in pairs}
                    counts["after_manifest_exclusions"] += int(not listed)
                    if rejected - listed:
                        counts["scene_exclusions_beyond_lists"] += 1
                    if not removals.keep(row):
                        rejected.add("label_removal")
                        counts["label_removal"] += 1
                    if rejected:
                        counts["removed"] += 1
                        continue
                    counts["eligible_before_source_policy"] += 1
                    if reason:
                        continue
                    row, changed = normalize_room(row, tok)
                    validate_source_row(row, kind)
                    counts["normalized_room_zero"] += int(changed)
                    types[typ] += 1
                    kept.append(index)
            if counts["seen"] != metadata["rows"]:
                raise ValueError("Pool source row count differs")
            expected_types = source.get("rows_per_type")
            if expected_types is not None and dict(original_types) != expected_types:
                raise ValueError("Pool source type counts differ")
            listed_qids = {qid for pairs in pool.lists.values() for source_name, qid in pairs if source_name == name}
            if not listed_qids <= seen:
                raise ValueError("Exclusion membership references absent source QIDs")
            expected = source.get("after_exclusions", {}).get("rows")
            if expected is not None and counts["after_manifest_exclusions"] != expected:
                raise ValueError("Pool declared post-exclusion count differs")
            observed = pool.scenes.sources[name]
            scene_reference = {kind: sum(source_name == name for source_name, _ in pool.lists[key])
                               for kind, key in (("dev", "dev_s1"), ("benchmark", "eval_rooms"))}
            record["scene_coverage"] = dict(reference=scene_reference,
                observed={kind: observed[kind+"_matches"] for kind in scene_reference}, status="FAIL")
            compare(pool.scenes.expected[name], observed, pool.scenes.files, name)
            record["scene_coverage"]["status"] = "PASS"
            if not reason:
                selection = output / ((digest(name) if opaque else name)+".json")
                write(selection, kept)
                record.update(selection=file_pin(selection), retained=len(kept), per_type=dict(types))
                if not kept:
                    record.update(status="DEFERRED", reason="empty_after_filters")
        except (ValueError, KeyError, TypeError, FileNotFoundError, gzip.BadGzipFile, EOFError) as exc:
            record.update(status="DEFERRED", reason=type(exc).__name__+": "+str(exc), retained=0)
            if isinstance(exc, SceneCoverageError):
                record["scene_integrity_failure"] = True
        record.update(counts=dict(counts), original_per_type=dict(original_types), removals=removals.report())
        sources[name] = record
        print(json.dumps(dict(source=digest(name), retained=record.get("retained", 0), status=record["status"])
                         if opaque else dict(pool_source=name, **record)), flush=True)
    report = dict(schema="s1-pool-selection-v1", manifest=manifest, room_sets=list(room_sets),
                  exclusions=pool.files, scene_exclusions=pool.scenes.files,
                  source_scene_exclusions=pool.scenes.report(validate=False),
                  blockers=[name for name, entry in sources.items() if entry.get("scene_integrity_failure")],
                  remove_files=Removals(remove_files, stream='vqa').files, tokenizer=tokenizer, sources=sources,
                  implementation=implementation(), training_admission=False, rgb_verified=False,
                  mask_shape_verified=False, scope="source-syntax-and-exclusions",
                  declared_rows=sum(value.get("declared_rows", 0) for value in sources.values()),
                  selected_rows=sum(value.get("retained", 0) for value in sources.values()
                                    if value["status"] == "ELIGIBLE"))
    write(output / "receipt.json", report)
    return report


def selected_rows(receipt_pin, name):
    receipt = load(pinned(receipt_pin))
    if receipt.get("schema") != "s1-pool-selection-v1" or receipt["implementation"] != implementation():
        raise ValueError("Pool selection implementation differs")
    if receipt.get("blockers"):
        raise SceneCoverageError("Pool scene integrity is blocked")
    pool = Pool(receipt["manifest"], receipt["room_sets"])
    if receipt["exclusions"] != pool.files or receipt["scene_exclusions"] != pool.scenes.files:
        raise ValueError("Pool exclusion bindings differ")
    source = receipt["sources"][name]
    if source["status"] != "ELIGIBLE" or pool.deferred(name):
        raise ValueError("Pool source is deferred")
    expected_scene_counts = scene_expectation(pool, name, source["declared_rows"], source["source"])
    if receipt["source_scene_exclusions"]["expected"][name] != expected_scene_counts:
        raise SceneCoverageError("Pool independent scene census differs from its membership lists")
    indices = load(pinned(source["selection"]))
    if (indices != sorted(set(indices)) or len(indices) != source["retained"]
            or any(type(index) is not int or index < 0 for index in indices)):
        raise ValueError("Pool selection indices differ")
    wanted = set(indices)
    removals = Removals(receipt["remove_files"], stream="vqa")
    tok = source_tokenizer(receipt["tokenizer"])
    count = 0
    with gzip.open(pinned(source["source"]), "rt") as stream:
        for index, line in enumerate(stream):
            row = json.loads(line)
            pool.scenes.keep(row, name)
            if index not in wanted:
                continue
            if pool.reasons(name, row):
                raise ValueError("Excluded pool row remains in the selection")
            removals.assert_clean(row)
            row, _ = normalize_room(row, tok)
            validate_source_row(row, source["kind"])
            count += 1
            yield row
    if count != len(indices):
        raise ValueError("Pool selection references absent rows")
    compare(expected_scene_counts, pool.scenes.sources[name], pool.scenes.files, name)
    if (receipt["source_scene_exclusions"]["files"] != pool.scenes.files
            or receipt["source_scene_exclusions"]["sources"][name] != pool.scenes.sources[name]
            or receipt["source_scene_exclusions"]["datasets"][name] != sorted(pool.scenes.datasets[name])):
        raise ValueError("Pool source scene census differs")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--remove-files", required=True)
    parser.add_argument("--tokenizer", required=True)
    args = parser.parse_args()
    result = prepare(file_pin(args.manifest), args.output, load(args.remove_files), file_pin(args.tokenizer))
    print(json.dumps(dict(selected_rows=result["selected_rows"], training_admission=False,
                          deferred={name: value["reason"] for name, value in result["sources"].items()
                                    if value["status"] != "ELIGIBLE"})))


if __name__ == "__main__":
    main()
