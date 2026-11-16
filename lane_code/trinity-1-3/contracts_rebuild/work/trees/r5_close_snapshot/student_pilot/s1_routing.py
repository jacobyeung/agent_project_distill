from collections import Counter
import copy
import gzip
import json
import math
from pathlib import Path
import random
import re
import sqlite3

from . import carrier_c1_routing as routing
from .p3_provenance import file_pin, load, pinned, write
from .training_contract import audit_training_contract
from trace_format.contracts import new_contracts, contract_identity, heading_plane_min


DIRECT_RULE = "S1-RD1"
FPS_RULE = "S1-FPS1"


def direct_transform(raw):
    answer = raw.get("answer")
    options = raw.get("student_input", {}).get("options")
    if (raw.get("question_type") != "route_planning" or raw.get("head_program") is not None
            or not isinstance(answer, str) or not re.fullmatch("[A-Z]", answer)
            or not isinstance(options, list)):
        raise ValueError("S1-RD1 requires a direct route-planning answer option")
    matches = [option[len(answer)+2:] for option in options
               if isinstance(option, str) and option.startswith(answer+". ")]
    if len(matches) != 1:
        raise ValueError("S1-RD1 cannot identify one unchanged answer option")
    empty = routing.THINK+"\n</think>\n\n"+answer
    if raw.get("target") == empty:
        return copy.deepcopy(raw), False
    target = raw.get("target", "")
    ending = "\n</think>\n\n"+answer
    if not target.startswith(routing.THINK) or not target.endswith(ending):
        raise ValueError("S1-RD1 requires the native answer envelope")
    original = target[len(routing.THINK):-len(ending)]
    match = re.fullmatch(r"(?:The turn is |The turns, in order, are )"
                         r"(Turn (?:Left|Right|Back)(?:, Turn (?:Left|Right|Back))*)\.", original)
    if match is None or match[1] != matches[0]:
        raise ValueError("S1-RD1 refuses reasoning or text other than the answer-option restatement")
    row = copy.deepcopy(raw)
    provenance = row.setdefault("provenance", {})
    if any(key in provenance for key in ("original_think", "direct_transform")):
        raise ValueError("S1-RD1 provenance already exists on an untransformed target")
    provenance.update(original_think=original, direct_transform=DIRECT_RULE)
    row["target"] = empty
    return row, True


def frame_request(row):
    provenance = row.get("provenance", {})
    pending = row.get("frames_pending", provenance.get("frames_pending"))
    if pending is None:
        dataset, scene = (provenance.get("alias") or routing.alias_of(provenance["canonical"])).split("/", 1)
        pending = dict(d=dataset, s=scene, i=provenance["frame_indices"])
    if (not isinstance(pending, dict) or pending.get("d") not in ("d1", "d2", "d3")
            or not isinstance(pending.get("s"), str) or not isinstance(pending.get("i"), list)
            or len(pending["i"]) != 32
            or any(type(index) is not int or index < 0 for index in pending["i"])
            or pending["i"] != sorted(set(pending["i"]))):
        raise ValueError("Routing requires 32 exact, ordered frame indices")
    return pending


class Frames:
    def __init__(self, map_pin, plan_pin, fps_by_scene=None, fps_authority=None, fps_by_dataset=None):
        self.pins = dict(map=map_pin, plan=plan_pin)
        self.frames = {}
        with gzip.open(pinned(map_pin), "rt") as stream:
            for line in stream:
                value = json.loads(line)
                key = value["d"], value["s"], value["i"]
                sha = value["sha256"]
                if (key in self.frames or not re.fullmatch("[0-9a-f]{64}", sha)
                        or value["path"] != "/data2/k6tk/"+sha[:2]+"/"+sha+".png"):
                    raise ValueError("RGB map has duplicate keys or a noncanonical content address")
                self.frames[key] = dict(path=value["path"], sha256=sha)
        with gzip.open(pinned(plan_pin), "rt") as stream:
            self.plan = json.load(stream)
        self.fps = {} if fps_by_scene is None else fps_by_scene
        self.dataset_fps = {key: set(values) for key, values in (fps_by_dataset or {}).items()}
        self.authority = None
        if fps_authority is not None:
            self.authority = load(pinned(fps_authority))
            if self.authority.get("schema") != "s1-fps-authority-v1":
                raise ValueError("Unknown frame-rate authority")
            self.pins["fps_authority"] = fps_authority
            for scene, value in self.authority["by_scene"].items():
                dataset, separator, name = scene.partition("/")
                if (dataset not in ("d1", "d2", "d3") or not separator or not name
                        or type(value) not in (float, int) or not math.isfinite(value) or value <= 0):
                    raise ValueError("Invalid pinned scene frame-rate authority")
                self.dataset_fps.setdefault(dataset, set()).add(value)

    def resolve(self, row):
        pending = frame_request(row)
        dataset, scene, indices = pending["d"], pending["s"], pending["i"]
        frames = [self.frames[dataset, scene, index] for index in indices]
        original = row.get("student_input", {})
        fps, fps_source = original.get("fps"), "source_row"
        observed = self.fps.get(dataset+"/"+scene)
        authorized = self.authority.get("by_scene", {}).get(dataset+"/"+scene) if self.authority else None
        if fps is None:
            fps, fps_source = observed, "native_scene_metadata"
        if fps is None and self.authority is not None:
            fps = authorized
            fps_source = "pinned_scene_authority"
        if fps is None and len(self.dataset_fps.get(dataset, ())) == 1:
            fps = next(iter(self.dataset_fps[dataset]))
            fps_source = "dataset_uniform"
        if (type(fps) not in (float, int) or not math.isfinite(fps) or fps <= 0
                or observed is not None and observed != fps or authorized is not None and authorized != fps):
            raise ValueError("Routing frame rate is missing, invalid or inconsistent with its native scene")
        video = self.plan["v"].get(scene)
        lower_bound = video is None or video.get("raw_n") is None
        if lower_bound:
            if dataset != "d3":
                raise ValueError("A video lacks its bound full frame count")
            total = max(indices)+1
        else:
            if video["g"] != dataset:
                raise ValueError("Frame-count authority names another dataset")
            total = video["raw_n"]
        if type(total) is not int or total <= max(indices):
            raise ValueError("Frame-count authority does not cover the requested anchors")
        if original.get("total_num_frames") is not None and original["total_num_frames"] != total:
            raise ValueError("Source frame count conflicts with its bound authority")
        if original.get("frame_indices") is not None and original["frame_indices"] != indices:
            raise ValueError("Source frame indices conflict with the pinned RGB request")
        if original.get("frames") and [value.get("sha256") for value in original["frames"]] != [
                value["sha256"] for value in frames]:
            raise ValueError("Source frame hashes conflict with the pinned RGB map")
        timestamps = [index/fps for index in indices]
        if original.get("timestamps") is not None and (
                not isinstance(original["timestamps"], list) or len(original["timestamps"]) != len(timestamps)
                or any(type(value) not in (int, float) or not math.isclose(value, expected, rel_tol=1e-9, abs_tol=1e-9)
                       for value, expected in zip(original["timestamps"], timestamps))):
            raise ValueError("Source timestamps conflict with the pinned frame rate")
        inputs = dict(original, frames=frames, frame_indices=indices, fps=float(fps),
                      timestamps=timestamps, total_num_frames=total)
        inputs.setdefault("question", row.get("question"))
        inputs.setdefault("options", row.get("options") or [])
        return inputs, dict(authority=self.pins, fps_rule=FPS_RULE, fps_source=fps_source,
                            total_num_frames_lower_bound=lower_bound)


def legacy_replay(row):
    raw = dict(row["routing"], schema="derivgen-row-v2", infrastructure_only=False,
               target=row["target"], trace_revision="3.14")
    routing.check_row(raw)
    if routing.rerender(raw, routing.RecordedGeometry(raw))[0] != row["target"]:
        raise ValueError("Native v3.14 execution changes stored program output")
    return True


def compatibility(database, receipt, pool_types, seed=17):
    counts = Counter()
    for key, count in receipt["types"].items():
        counts[key.rsplit(":", 1)[0]] += count
    wanted = {kind: min(200, count) for kind, count in counts.items() if kind not in pool_types}
    sampled, equal, errors, indices = Counter(), Counter(), {}, {}
    path = pinned(database)
    connection = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)
    try:
        if connection.execute("SELECT count(*) FROM rows").fetchone()[0] != receipt["count"]:
            raise ValueError("Legacy routing count differs from its native receipt")
        for index in random.Random(seed).sample(range(receipt["count"]), receipt["count"]):
            if all(sampled[kind] == quota for kind, quota in wanted.items()):
                break
            row = json.loads(connection.execute("SELECT row FROM rows WHERE i=?", (index,)).fetchone()[0])
            kind = row["routing"]["question_type"]
            if sampled[kind] >= wanted.get(kind, 0):
                continue
            sampled[kind] += 1
            indices.setdefault(kind, []).append(index)
            try:
                legacy_replay(row)
                equal[kind] += 1
            except (ValueError, KeyError, TypeError, IndexError) as error:
                errors.setdefault(kind, []).append(dict(index=index, qid=row["qid"],
                                                       error=type(error).__name__+": "+str(error)))
    finally:
        connection.close()
    return {kind: dict(source_rows=count,
        disposition="DROPPED" if kind in pool_types else
                    "COMPATIBLE" if equal[kind] == sampled[kind] == wanted[kind] else "DEFERRED",
        reason="pool_type_wins" if kind in pool_types else
               None if equal[kind] == sampled[kind] == wanted[kind] else "v314_execution_disagreement",
        tested=sampled[kind], exact_execution_agreement=equal[kind], sample_indices=indices.get(kind, []),
        errors=errors.get(kind, [])[:20]) for kind, count in counts.items()}


def build(cfg, directory, division_pin, base_model, *, audit_only=False):
    from trace_format.contracts import contract_epoch
    with contract_epoch(cfg.get('contract_epoch', new_contracts()), heading_plane_min=cfg.get('heading_plane_min', heading_plane_min())):
        return _build(cfg, directory, division_pin, base_model, audit_only=audit_only)


def _build(cfg, directory, division_pin, base_model, *, audit_only=False):
    from . import s1_pool
    from .carrier_c1_run import division_admits, processor_for_receipt
    from .row_removals import Removals
    from .s1_exclusions import Exclusions, totals
    from .s1_scene_census import SceneCoverageError
    from .s1_route_policy import validate as validate_policy
    route_policy = validate_policy(cfg)
    spec = cfg["s1_routing"]
    if spec.get("schema") != "s1-routing-inputs-v1":
        raise ValueError("Unknown S1 routing materialization contract")
    output = Path(directory)
    output.mkdir()
    from .s1_pool_relocate import relocate
    model = load(pinned(base_model))
    if not audit_only and model.get("kind") != "base":
        raise ValueError("Materialized routing requires the actual pinned base-model manifest")
    tokenizer = file_pin(Path(model["root"]) / "tokenizer.json")
    relocation = relocate(spec["selection"], spec.get("catalog", {}), output / "pool", tokenizer=tokenizer)
    selection_pin = relocation["relocated"]
    selection = load(pinned(selection_pin))
    contract_manifest = load(pinned(spec['candidate_manifest'])) if spec.get('candidate_manifest') else None
    if selection["implementation"] != s1_pool.implementation():
        raise ValueError("Routing selection belongs to another implementation")
    if selection.get("blockers"):
        raise SceneCoverageError("Routing pool scene integrity is blocked")
    legacy = load(pinned(cfg["streams"]["routing"]))
    if not division_admits(legacy["division"], division_pin) or legacy.get("scene_role", "train") != "train":
        raise ValueError("Routing materialization must retain the native training division")
    division = load(pinned(division_pin))
    if division.get("schema") != "diagnostic-whole-scene-division-v1" or division.get("training_only") is not True:
        raise ValueError("Routing needs the native training-only scene division")
    train, heldout = set(division["train_scenes"]), set(division["heldout_scenes"])
    pool_types = {kind for value in selection["sources"].values() if value["status"] == "ELIGIBLE"
                  for kind, count in value["per_type"].items() if count and (
                      route_policy is None or cfg["route_table"].get(kind, "direct") == "route"
                      or value["kind"] == "rows" and kind == "route_planning")}
    legacy_check = compatibility(legacy["database"], legacy, pool_types)
    processor = processor_for_receipt(model, cfg)
    tokens = processor._routing_tokens
    filters = Exclusions(cfg["dev_scene_exclusions"], cfg["benchmark_scene_exclusions"])
    removals = Removals(cfg["remove_files"])
    database = output / "rows.sqlite"
    connection = sqlite3.connect(":memory:" if audit_only else database)
    if audit_only:
        connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute("CREATE TABLE candidates (k INTEGER PRIMARY KEY, qid TEXT NOT NULL, question_type TEXT NOT NULL, origin TEXT NOT NULL, source TEXT NOT NULL, row TEXT NOT NULL)")
    connection.execute("CREATE INDEX candidate_qids ON candidates(qid,origin)")
    connection.execute("CREATE INDEX candidate_order ON candidates((origin='legacy'),k)")
    connection.execute("CREATE TABLE pool_qids (qid TEXT PRIMARY KEY)")
    connection.execute("CREATE TABLE membership (i INTEGER PRIMARY KEY,k INTEGER UNIQUE NOT NULL)")
    connection.execute("CREATE VIEW rows AS SELECT m.i,c.row,'{}' AS target FROM membership m JOIN candidates c ON c.k=m.k")
    stats, fps, dataset_fps, direct_audit = {}, {}, {}, {}
    source_deferrals = {}
    contract_deferred_qids = {}
    current_qid = None
    sequence = 0

    def count(kind, key, reason=None):
        value = stats.setdefault(kind, dict(pool_program_rows=0, direct_rows=0, r16_kept=0,
                                            r16_dropped={}, r16_deferred={}, pool_deferred={}))
        if reason is None:
            value[key] += 1
        else:
            value[key][reason] = value[key].get(reason, 0)+1
            if key.endswith('_deferred'):
                entry = contract_deferred_qids.setdefault(reason, dict(count=0, qids=[]))
                entry['count'] += 1
                if len(entry['qids']) < 50:
                    entry['qids'].append(str(current_qid))

    def reason(row, source):
        key = row["dataset"]+"/"+row["scene"]
        if key not in train or key in heldout:
            return "outside_native_training_division"
        if not filters.keep(row, source):
            return "scene_exclusion"
        if not removals.keep(row):
            return "label_removal"
        kind = row["routing"]["question_type"]
        expected = "route" if row["routing"]["tool_output_spans"] else "direct"
        if route_policy is not None:
            if expected == "route" and cfg["route_table"].get(kind, "direct") != "route":
                return "program_type_not_allowlisted"
            if expected == "direct" and (kind != "route_planning"
                                        or cfg["route_table"].get(kind, "direct") != "direct"):
                return "direct_routing_type_not_allowed"
        elif cfg["route_table"].get(kind) != expected:
            return "route_policy_mismatch"
        return None

    def add(row, origin, source):
        nonlocal sequence
        refusal = audit_training_contract([row], contract_manifest)[0]
        if refusal:
            routing_info = row.get('routing')
            kind = routing_info.get('question_type', 'unknown') if isinstance(routing_info, dict) else 'unknown'
            count(kind, 'r16_deferred' if origin == 'legacy' else 'pool_deferred', refusal)
            return
        if new_contracts() and contract_manifest is not None and str(row['qid']) in contract_manifest:
            from .phrases import phrase_set
            entry = contract_manifest[str(row['qid'])]
            row['candidate_phrases'] = list(phrase_set(entry.get('phrases', []) if isinstance(entry, dict) else entry))
        spans = routing.render(row["routing"]["events"], row["routing"]["answer"])[1] if row["routing"]["events"] else []
        ids, _, _ = routing.suffix_tokens(processor, row, row["target"], spans)
        if len(ids) > cfg["recipe"].get("max_routing_suffix_tokens", 9600):
            raise ValueError("Routing suffix exceeds the unchanged native token limit")
        connection.execute("INSERT INTO candidates VALUES (?,?,?,?,?,?)",
                           (sequence, row["qid"], row["routing"]["question_type"], origin, source, json.dumps(row)))
        sequence += 1

    try:
        path = pinned(legacy["database"])
        source = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)
        observed_types = Counter()
        try:
            def census_rows():
                for (encoded,) in source.execute("SELECT row FROM rows ORDER BY i"):
                    row = json.loads(encoded)
                    filters.census.identities(row)
                    key = row["dataset"]+"/"+row["scene"]
                    if (legacy_check[row["routing"]["question_type"]]["disposition"] == "COMPATIBLE"
                            and key in train and key not in heldout):
                        yield row

            filters.expect("r16", census_rows(), dict(database=legacy["database"], division=division_pin,
                                                     compatibility=legacy_check))
            for (encoded,) in source.execute("SELECT row FROM rows ORDER BY i"):
                row = json.loads(encoded)
                current_qid = row.get("qid")
                observed_types[row["routing"]["question_type"]+":"+row["routing"]["category"]] += 1
                key = row["dataset"]+"/"+row["scene"]
                value = row.get("student_input", {}).get("fps")
                if type(value) in (float, int) and math.isfinite(value) and value > 0:
                    fps[key] = value if key not in fps or fps[key] == value else "conflicting_rates"
                    dataset_fps.setdefault(row["dataset"], set()).add(value)
                kind = row["routing"]["question_type"]
                verdict = legacy_check[kind]
                if verdict["disposition"] != "COMPATIBLE":
                    count(kind, "r16_dropped" if verdict["disposition"] == "DROPPED" else "r16_deferred",
                          verdict["reason"])
                    continue
                refusal = reason(row, "r16")
                if refusal:
                    count(kind, "r16_deferred" if refusal in ("program_type_not_allowlisted",
                                                            "direct_routing_type_not_allowed")
                          else "r16_dropped", refusal)
                    continue
                try:
                    add(row, "legacy", "r16")
                except (ValueError, KeyError, TypeError) as error:
                    count(kind, "r16_deferred", str(error))
        finally:
            source.close()
        if dict(observed_types) != legacy["types"]:
            raise ValueError("Legacy routing type counts differ from its receipt")
        frames = Frames(spec["frame_map"], spec["frame_plan"], fps,
                        spec.get("fps_authority"), dataset_fps)
        for name, entry in selection["sources"].items():
            if entry["status"] != "ELIGIBLE":
                source_deferrals[name] = dict(reason=entry["reason"], rows=entry["declared_rows"])
                continue
            scene_source = "pool/"+name
            filters.counts(scene_source)
            filters.expected[scene_source] = dict(schema="s1-scene-census-v1",
                method="subset-of-independently-checked-pool-selection", files=filters.files,
                rows=None, reference=selection_pin, source=name,
                counts=dict(dev_matches=0, benchmark_matches=0, overlap_matches=0))
            if entry["kind"] == "rows":
                audit = dict(rows=0, transformed=0, passed=0, deferred=0, reasons={})
                with gzip.open(pinned(entry["source"]), "rt") as stream:
                    for line in stream:
                        audit["rows"] += 1
                        raw = json.loads(line)
                        try:
                            transformed, changed = direct_transform(raw)
                            inputs, _ = frames.resolve(transformed)
                            routing.direct_row({**transformed, "student_input": inputs})
                            audit["transformed"] += int(changed)
                            audit["passed"] += 1
                        except (ValueError, KeyError, TypeError) as error:
                            audit["deferred"] += 1
                            text = type(error).__name__+": "+str(error)
                            audit["reasons"][text] = audit["reasons"].get(text, 0)+1
                direct_audit[name] = audit
            for raw in s1_pool.selected_rows(selection_pin, name):
                current_qid = raw.get("qid")
                kind = raw["question_type"]
                if connection.execute("SELECT 1 FROM pool_qids WHERE qid=?", (raw["qid"],)).fetchone():
                    count(kind, "pool_deferred", "duplicate_pool_qid")
                    continue
                connection.execute("INSERT INTO pool_qids VALUES (?)", (raw["qid"],))
                try:
                    refusal = audit_training_contract([raw], contract_manifest)[0]
                    if refusal:
                        count(kind, "pool_deferred", refusal)
                        continue
                    changed = False
                    if entry["kind"] == "rows":
                        raw, changed = direct_transform(raw)
                    inputs, frame_binding = frames.resolve(raw)
                    if entry["kind"] == "rows":
                        row = routing.direct_row({**raw, "student_input": inputs})
                    else:
                        rgb = dict(frames=[{**pin, "source_index": index} for pin, index
                                           in zip(inputs["frames"], inputs["frame_indices"], strict=True)],
                                   fps=inputs["fps"], total_num_frames=inputs["total_num_frames"])
                        row = routing.c1_row(raw, rgb)
                    for binding_key in ('batch_cache_phrases', 'candidate_phrases', 'candidate_manifest', 'cache_phrases', 'uses_mask_cache', 'mask_source'):
                        if binding_key in raw:
                            row[binding_key] = raw[binding_key]
                    row["s1_source"] = dict(name=name, source=entry["source"], frame_binding=frame_binding,
                        direct_transform=DIRECT_RULE if changed else None, provenance=raw.get("provenance", {}),
                        flags={key: raw[key] for key in ("training_admitted", "infrastructure_only",
                            "score_nomination_allowed", "benchmark_trained_diagnostic", "provisional_diagnostic")
                               if key in raw})
                    refusal = reason(row, scene_source)
                    if refusal:
                        count(kind, "pool_deferred", refusal)
                        continue
                    add(row, "pool_direct" if entry["kind"] == "rows" else "pool_program", name)
                except SceneCoverageError:
                    raise
                except (ValueError, KeyError, TypeError) as error:
                    count(kind, "pool_deferred", type(error).__name__+": "+str(error))
        membership, scenes, layouts, types = 0, set(), Counter(), Counter()
        frame_rate_sources = {}
        for key, qid, kind, origin, encoded in connection.execute(
                "SELECT k,qid,question_type,origin,row FROM candidates ORDER BY origin='legacy',k"):
            if origin == "legacy" and connection.execute("SELECT 1 FROM pool_qids WHERE qid=?", (qid,)).fetchone():
                count(kind, "r16_dropped", "pool_qid_wins")
                continue
            row = json.loads(encoded)
            connection.execute("INSERT INTO membership VALUES (?,?)", (membership, key))
            membership += 1
            count(kind, "r16_kept" if origin == "legacy" else
                  "direct_rows" if origin == "pool_direct" else "pool_program_rows")
            scenes.add(row["dataset"]+"/"+row["scene"])
            layouts[row["routing"]["head_layout"]] += 1
            types[kind+":"+row["routing"]["category"]] += 1
            if origin != "legacy":
                frame_rate_sources.setdefault(row["dataset"], Counter())[
                    row["s1_source"]["frame_binding"]["fps_source"]] += 1
        connection.commit()
    finally:
        connection.close()
    blockers = []
    if any(value["deferred"] > .01*value["rows"] for value in direct_audit.values()):
        blockers.append("direct_schema_failure_exceeds_one_percent")
    if not any(value["pool_program_rows"] for value in stats.values()):
        blockers.append("no_admitted_pool_program_rows")
    scene_report = filters.report()
    pool_report = copy.deepcopy(selection["source_scene_exclusions"])
    for key in ("sources", "datasets", "expected"):
        pool_report[key] = {name: value for name, value in pool_report[key].items()
                            if selection["sources"][name]["status"] == "ELIGIBLE"}
    scene_report["upstream"] = dict(pool=pool_report)
    totals(scene_report, filters)
    materialization = dict(schema="s1-routing-materialization-v1",
        status="BLOCKED" if blockers else "METADATA_ONLY" if audit_only else "PASS",
        inputs=spec, legacy=cfg["streams"]["routing"], division=division_pin, direct_rule=DIRECT_RULE,
        base_model=base_model, **contract_identity(),
        relocation=file_pin(output / "pool/relocation.json"), resolved_selection=selection_pin,
        direct_rule_audit=direct_audit, legacy_compatibility=legacy_check, types=stats,
        source_denominator=selection["declared_rows"]+legacy["count"], source_deferrals=source_deferrals, contract_deferred_qids=contract_deferred_qids,
        pool_selection_counts={name: {key: value[key] for key in ("declared_rows", "original_per_type", "per_type",
            "retained", "counts", "status", "reason") if key in value} for name, value in selection["sources"].items()},
        fps_rule=FPS_RULE, fps_policy="source_then_scene_then_uniform_authority_dataset",
        native_fps_by_dataset={key: sorted(values) for key, values in dataset_fps.items()},
        authority_fps_by_dataset={key: sorted(values) for key, values in frames.dataset_fps.items()},
        frame_rate_sources={key: dict(values) for key, values in frame_rate_sources.items()},
        blockers=blockers, native_rows=membership, audit_only=audit_only,
        source_scene_exclusions=scene_report,
        **({"s1_route_policy": route_policy} if route_policy is not None else {}),
        frame_bytes_verified=False, production_authorized=False)
    write(output / "materialization.json", materialization)
    if audit_only:
        return materialization
    receipt = dict(schema=routing.ROUTING_SCHEMA, stream="routing", count=membership, scenes=len(scenes),
        types=dict(types), division=division_pin, database=file_pin(database), scene_role="train", heldout_overlap=0,
        policy_version="s1-pool-first-v1", policy=cfg["route_table"], routing_tokens=tokens["ids"],
        head_layouts=dict(layouts), allow_paired_anchor=True, source=spec["selection"],
        materialization=file_pin(output / "materialization.json"), direct_rule=DIRECT_RULE,
        fps_rule=FPS_RULE, frame_rate_sources=materialization["frame_rate_sources"],
        **({"s1_route_policy": route_policy} if route_policy is not None else {}),
        removals=removals.report(), source_scene_exclusions=scene_report)
    write(output / "receipt.json", receipt)
    if blockers or not membership:
        raise ValueError("S1 routing materialization is blocked: "+", ".join(blockers or ["empty_routing"]))
    return receipt
