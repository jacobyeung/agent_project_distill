from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import native_common as C
import chain_save as A
import kernels as K


FAMILY_COUNTS = dict(object_abs_distance=150, room_size_estimation=36,
                     camera_displacement=150, camera_movement_direction=150, camera_rotation=150)
GEOMETRY_CAPTURES = 84
GEOMETRY_REFUSAL_POLICY = "bound-per-capture-geometry-refusals-v1"
GEOMETRY_REFUSAL_CODE = "reference_camera_up_opposes_gravity"
RETURN_LIMIT = 256*1024**2-16*1024
EXPANDED_LIMIT = 512*1024**2
FIXED_RESERVE = 16*1024**2


class CounterStream:
    def __init__(self):
        self.bytes = 0

    def write(self, data):
        self.bytes += len(data)
        return len(data)

    def flush(self):
        pass


def measure(paths, root):
    files = sorted(path for entry in paths for path in A.regular_files(entry))
    if len(set(files)) != len(files):
        raise ValueError("Return measurement repeats a file")
    raw = sum(path.stat().st_size for path in files)
    sink = CounterStream()
    if files:
        with gzip.GzipFile(fileobj=sink, mode="wb", compresslevel=6, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                for path in files:
                    archive.add(path, arcname=str(path.relative_to(root)), recursive=False)
    return dict(raw_bytes=raw, tar_gzip_bytes=sink.bytes, files=len(files))


def pair_size(pair, grounding, root, digested_pair=None):
    journal = "".join(json.dumps(row, allow_nan=False)+"\n" for row in pair).encode()
    digested = "".join(json.dumps(row, allow_nan=False)+"\n" for row in (
        pair if digested_pair is None else digested_pair)).encode()
    return dict(journal_raw_bytes=len(journal),
                journal_gzip_bytes=len(gzip.compress(journal, compresslevel=6, mtime=0)),
                digested_journal_raw_bytes=len(digested),
                digested_journal_gzip_bytes=len(gzip.compress(digested, compresslevel=6, mtime=0)),
                grounding=measure([grounding] if grounding.exists() else [], root))


def refusal_size(rows):
    groups = defaultdict(list)
    aliases = dict(absolute_distance_object="object_abs_distance", absolute_size_room="room_size_estimation")
    for row in rows:
        if (not row.get("geometry_refusal") or row.get("decode_executed") is not False
                or "decode" in row or row.get("called") is not False
                or row.get("call_errors") or row.get("version_errors")
                or any(value not in (None, 0.) for value in row["scores"].values())):
            raise ValueError("A geometry-refused row decoded or scored a nonzero result")
        name = aliases.get(row["question_type"], row["question_type"])
        if name not in FAMILY_COUNTS:
            raise ValueError("A geometry refusal is outside the full cohort")
        groups[name].append(row)
    result = {}
    for name in FAMILY_COUNTS:
        values = groups[name]
        identities = [(row["key"], row["arm"]) for row in values]
        keys = {key for key, arm in identities}
        if (len(identities) != len(set(identities))
                or set(identities) != {(key,arm) for key in keys for arm in ("unflagged", "scripted")}):
            raise ValueError("Geometry refusal arm/item membership differs")
        data = "".join(json.dumps(row, allow_nan=False, sort_keys=True)+"\n" for row in values).encode()
        result[name] = dict(items=len(keys), raw_bytes=len(data),
                            gzip_bytes=len(gzip.compress(data, compresslevel=6, mtime=0)) if data else 0)
    return result


def geometry_evidence(report):
    geometry = report.get("geometry", [])
    candidates = report.get("full_item_candidates", [])
    if (report.get("geometry_refusal_policy") != GEOMETRY_REFUSAL_POLICY
            or len(geometry) != GEOMETRY_CAPTURES
            or len({row["native"] for row in geometry}) != GEOMETRY_CAPTURES
            or any(row.get("status") not in ("PASS", "REFUSED") for row in geometry)
            or len(candidates) != 636 or len({row["key"] for row in candidates}) != 636
            or {row["native"] for row in candidates} != {row["native"] for row in geometry}
            or Counter(row["family"] for row in candidates) != Counter(FAMILY_COUNTS)):
        raise ValueError("The full geometry evidence differs from its 84-capture/636-item cohort")
    refused_captures = {row["native"]:row for row in geometry if row["status"] == "REFUSED"}
    expected_refusals = {row["key"]:row for row in candidates if row["native"] in refused_captures}
    refusal_rows = report.get("geometry_refusal_records", [])
    identities = [(row["key"], row["arm"]) for row in refusal_rows]
    if (len(identities) != len(set(identities))
            or set(identities) != {(key,arm) for key in expected_refusals for arm in ("unflagged", "scripted")}):
        raise ValueError("The full geometry evidence omitted a refused item or arm")
    for row in refusal_rows:
        capture = refused_captures[expected_refusals[row["key"]]["native"]]
        recorded = {key:value for key,value in capture.items() if key not in ("return_size", "refused_items_by_arm")}
        refusal = row.get("geometry_refusal", {})
        if (refusal.get("capture") != capture["native"] or refusal.get("checkpoint") != report["artifact"]
                or refusal.get("code") != GEOMETRY_REFUSAL_CODE
                or refusal.get("capture_record_sha256") != C.canonical(recorded)
                or refusal.get("code") != capture["error"]["code"]
                or refusal.get("message") != capture["error"]["message"]
                or row.get("binding") != report.get("request_binding")):
            raise ValueError("An item refusal differs from the bound capture")
    refused_sizes = refusal_size(refusal_rows)
    refused_counts = Counter(row["family"] for row in expected_refusals.values())
    if (dict(refused_counts) != report.get("geometry_refused_items")
            or refused_sizes != report.get("refusal_return_size")):
        raise ValueError("The geometry refusal counts or sizes differ")
    served_counts = {name:count-refused_counts[name] for name,count in FAMILY_COUNTS.items()}
    return served_counts, refused_counts, refused_sizes


class PilotReport:
    def __init__(self, path, config, cuda):
        self.path, self.cuda = Path(path), cuda
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.value = dict(
            schema="evalx-unscored-native-pilot-report-v1", synthetic=False, complete=False,
            training_decision_allowed=False, full_read_authorized=False,
            family_sha256=config["family"]["sha256"], plan_sha256=config["plan_sha256"],
            artifact=config["worker"]["artifact"], selection=config["worker"]["pilot_selection"],
            registered_selection=config["worker"]["pilot_selection"],
            reader_semantics=dict(C.REPORT_SEMANTICS),
            full_family_counts=FAMILY_COUNTS, full_geometry_captures=GEOMETRY_CAPTURES,
            load_seconds=None, parity_seconds=None, geometry=[], items=[],
            peak_memory_scope="PyTorch allocation peaks; allocator/driver sampling is separate",
            return_size_scope="Measured level-6 gzip categories; the publisher records the actual return")
        self.checkpoint("starting")

    def checkpoint(self, phase, **values):
        self.value.update(values, phase=phase,
                          peak_allocated_bytes=self.cuda.max_memory_allocated(),
                          peak_reserved_bytes=self.cuda.max_memory_reserved())
        groups = defaultdict(list)
        for item in self.value["items"]:
            groups[item["family"]].append(item)
        self.value["by_family"] = dict(groups)
        geometry = self.value["geometry"]
        self.value["geometry_seconds_per_capture"] = (
            sum(row["seconds"] for row in geometry)/len(geometry) if geometry else None)
        self.value["capped_timing_observed"] = any(row["capped"] for row in self.value["items"])
        first = next((row for row in self.value["items"] if row.get("decode_budget", {}).get("fired")), None)
        if first is not None and self.value.get("first_budgeted_item") is None:
            budget = first["decode_budget"]
            record = dict(key=first["key"], **{key: budget[key] for key in (
                "close_token_ids", "close_token_pieces", "trigger_position",
                "forced_close_position", "deferred_sampled_tokens", "forced_budget_tokens")})
            self.value["first_budgeted_item"] = record
            print(json.dumps(dict(event="first_budgeted_item", **record), sort_keys=True), flush=True)
        self.value.setdefault("first_budgeted_item", None)
        A.atomic_json(self.path, self.value)
        return self.value


def nonnegative(value):
    if type(value) is not int or value < 0:
        raise ValueError("Pilot byte and file counts must be nonnegative integers")
    return value


SCENARIOS = ("none_capped", "replay_estimated", "all_capped")


def project(report, scenario=None):
    if scenario is not None and scenario not in SCENARIOS:
        raise ValueError("Unknown full-read projection scenario")
    items, geometry = report.get("items", []), report.get("geometry", [])
    selection = report.get("selection", {})
    if (report.get("schema") != "evalx-unscored-native-pilot-report-v1"
            or report.get("synthetic") is not False or report.get("complete") is not True
            or report.get("training_decision_allowed") is not False
            or report.get("full_read_authorized") is not False or report.get("parity_pass") is not True
            or report.get("full_family_counts") != FAMILY_COUNTS
            or report.get("full_geometry_captures") != GEOMETRY_CAPTURES
            or report.get("geometry_refusal_policy") != GEOMETRY_REFUSAL_POLICY
            or len(items) != 10 or len(geometry) != GEOMETRY_CAPTURES
            or len({row["native"] for row in geometry}) != GEOMETRY_CAPTURES
            or [row["key"] for row in items] != selection.get("item_keys")
            or len(set(selection.get("item_keys", []))) != 10
            or Counter(row["family"] for row in items) != Counter(K.PILOT_COUNTS)
            or selection.get("families") != K.PILOT_COUNTS
            or selection != K.select_geometry_pilot(report.get("full_item_candidates", []),
                                                    report.get("registered_selection", {}), geometry)):
        raise ValueError("Full projection requires the registered ten-pair sample and all 84 capture dispositions")
    served_counts, refused_counts, refused_sizes = geometry_evidence(report)
    refused_keys = set(selection["refused_item_keys"])
    for row in items:
        refused = row["key"] in refused_keys
        if bool(row.get("geometry_refusal")) != refused:
            raise ValueError("The sampled refusal membership differs")
        if refused and (row.get("decode_executed") is not False or row.get("generated_tokens") != 0
                        or row.get("native_seconds") != 0 or row.get("finish") != "geometry_refusal"
                        or row.get("call_errors") or row.get("capped") or row.get("decode_budget")):
            raise ValueError("The sampled geometry refusal executed decoding")
    items = [row for row in items if row["key"] not in refused_keys]
    budget = dict(thinking_tokens=2048, answer_tokens=64, max_new_tokens=16384,
                  max_calls=200, call_window_tokens=96, counting="sampled_callbacks")
    if (report.get("decode_budget") != budget or report.get("query_journal_retain_per_type") != 3
            or report.get("reader_semantics") != C.REPORT_SEMANTICS):
        raise ValueError("The pilot reader budget or query-journal policy differs")
    close_lengths = [len(row.get("decode_budget", {}).get("close_token_ids", [])) for row in items]
    close_tokens = max(close_lengths)
    if close_tokens < 1:
        raise ValueError("The pilot has no measured forced-closing tokenization")
    sampled_limit = budget["thinking_tokens"] + budget["call_window_tokens"] + close_tokens + budget["answer_tokens"] + 1
    grouped = defaultdict(list)
    for row in items:
        grouped[row["family"]].append(row)
    compressed = raw = files = 0
    per_family = {}
    for name, total_count in FAMILY_COUNTS.items():
        count = served_counts[name]
        sizes = [row["return_size"] for row in grouped[name]]
        journal = max(nonnegative(row["journal_gzip_bytes"]) for row in sizes)
        journal_raw = max(nonnegative(row["journal_raw_bytes"]) for row in sizes)
        if any("digested_journal_gzip_bytes" not in row or "digested_journal_raw_bytes" not in row
               for row in sizes):
            raise ValueError("The pilot lacks digested-row size measurements")
        digested = max(nonnegative(row["digested_journal_gzip_bytes"]) for row in sizes)
        digested_raw = max(nonnegative(row["digested_journal_raw_bytes"]) for row in sizes)
        grounding = max(nonnegative(row["grounding"]["tar_gzip_bytes"]) for row in sizes)
        grounding_raw = max(nonnegative(row["grounding"]["raw_bytes"]) for row in sizes)
        count_files = max(nonnegative(row["grounding"]["files"]) for row in sizes)
        per_family[name] = dict(items=total_count, decoded_items=count,
                               geometry_refused_items=refused_counts[name], geometry_refusal_decode_seconds=0.,
                               sample_items=len(sizes),
                               maximum_pair_gzip_bytes=journal, maximum_grounding_gzip_bytes=grounding,
                               retained_full_items=min(3, count), digested_items=max(0, count-3),
                               maximum_digested_pair_gzip_bytes=digested)
        compressed += 2*(min(3,count)*journal+max(0,count-3)*digested)+count*grounding
        raw += 2*(min(3,count)*journal_raw+max(0,count-3)*digested_raw)+count*grounding_raw
        files += count*count_files
        compressed += 2*refused_sizes[name]["gzip_bytes"]
        raw += 2*refused_sizes[name]["raw_bytes"]
        bounds, ordinary = [], []
        for row in grouped[name]:
            timing = row.get("decode_budget", {})
            sampled = nonnegative(timing.get("sampled_tokens", 0))
            injected = nonnegative(timing.get("injected_tokens", 0))
            total = nonnegative(row.get("generated_tokens", 0))
            capped = (timing.get("fired") is True or row.get("finish") in
                      ("call_limit", "max_new_tokens", "context_exhaustion"))
            if (not sampled or sampled+injected != total or row["capped"] is not capped
                    or timing.get("total_tokens", total) != total
                    or any(not math.isfinite(row[field]) or row[field] < 0
                           for field in ("seconds", "native_seconds"))
                    or row["native_seconds"] > row["seconds"]):
                raise ValueError("The pilot token counts or timing components differ")
            limit = (budget["max_new_tokens"] if capped and timing.get("natural_close")
                     and not timing.get("fired") else sampled_limit)
            rate = row["native_seconds"]/sampled
            overhead = row["seconds"]-row["native_seconds"]
            bounds.append(dict(key=row["key"], family=name, sampled_tokens=sampled, capped=capped,
                               sampled_slot_limit=limit, seconds_per_sampled_token=rate,
                               measured_overhead_seconds=overhead, measured_seconds=row["seconds"],
                               capped_seconds=max(row["seconds"], limit*rate+overhead)))
            if not capped:
                ordinary.append(row["seconds"])
        bounded_mean = sum(row["capped_seconds"] for row in bounds)/len(bounds)
        ordinary_mean = sum(ordinary)/len(ordinary) if ordinary else bounded_mean
        capped_pilot = sum(row["capped"] for row in bounds)
        per_family[name].update(
            pilot_capped_items=capped_pilot, replay_estimated_capped_items=math.ceil(count*capped_pilot/len(bounds)),
            ordinary_pair_seconds=ordinary_mean, capped_pair_seconds=max(ordinary_mean, bounded_mean),
            ordinary_basis="mean uncapped pilot time" if ordinary else "budget bound; no uncapped pilot observation",
            item_time_bounds=bounds)
    compressed += sum(nonnegative(row["return_size"]["tar_gzip_bytes"]) for row in geometry)
    raw += sum(nonnegative(row["return_size"]["raw_bytes"]) for row in geometry)
    files += sum(nonnegative(row["return_size"]["files"]) for row in geometry)
    fixed = report["fixed_return_size"]
    compressed += nonnegative(fixed["tar_gzip_bytes"])
    raw += nonnegative(fixed["raw_bytes"])
    files += nonnegative(fixed["files"])+64
    projected = math.ceil(1.5*compressed)+FIXED_RESERVE
    expanded = math.ceil(1.5*raw)+FIXED_RESERVE
    geometry_seconds = report["geometry_seconds"]
    times = [geometry_seconds]+[row["seconds"] for row in geometry]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in times):
        raise ValueError("The geometry timings must be finite and nonnegative")
    if geometry_seconds < sum(row["seconds"] for row in geometry):
        raise ValueError("The geometry phase is shorter than its capture timings")
    overhead = 2*report["load_seconds"]+report["parity_seconds"]+geometry_seconds
    if not math.isfinite(overhead) or overhead < 0:
        raise ValueError("Pilot timing projection is not finite and nonnegative")
    size_fits = projected <= RETURN_LIMIT and expanded <= EXPANDED_LIMIT and files < 10000
    scenarios = {}
    for label in SCENARIOS:
        capped_counts = {name: (0 if label == "none_capped" else count if label == "all_capped"
                               else per_family[name]["replay_estimated_capped_items"])
                         for name, count in served_counts.items()}
        seconds = overhead+sum(
            (count-capped_counts[name])*per_family[name]["ordinary_pair_seconds"]+
            capped_counts[name]*per_family[name]["capped_pair_seconds"] for name, count in served_counts.items())
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("A pilot timing scenario is not finite and nonnegative")
        with_margin = math.ceil(1.5*seconds)
        scenarios[label] = dict(capped_by_family=capped_counts, capped_items=sum(capped_counts.values()),
                               full_time_seconds_before_margin=seconds,
                               full_time_seconds_with_margin=with_margin,
                               geometry_refused_items=sum(refused_counts.values()),
                               geometry_refusal_decode_seconds=0.,
                               time_fits=with_margin <= 21600, fits=size_fits and with_margin <= 21600)
    selected = scenarios.get(scenario)
    return dict(
        schema="evalx-native-full-projection-v1", projected_compressed_bytes=projected,
        projected_expanded_bytes=expanded, projected_files=files,
        compressed_limit=RETURN_LIMIT, expanded_limit=EXPANDED_LIMIT,
        fits=selected["fits"] if selected else False, size_fits=size_fits,
        time_fits=selected["time_fits"] if selected else False,
        projection_scenario=scenario, scenario_required=True, scenarios=scenarios,
        reader_semantics=dict(C.REPORT_SEMANTICS),
        allocation_seconds=21600,
        per_family=per_family, geometry_captures=GEOMETRY_CAPTURES,
        safety_factor=1.5, fixed_reserve_bytes=FIXED_RESERVE, journal_and_bundle_copies=2,
        query_journal_retain_per_type=3,
        full_time_seconds_before_margin=selected["full_time_seconds_before_margin"] if selected else None,
        full_time_seconds_with_margin=selected["full_time_seconds_with_margin"] if selected else None,
        item_time_bounds=[row for group in per_family.values() for row in group["item_time_bounds"]],
        pilot_sample_refused_items=len(refused_keys), pilot_sample_decoded_items=len(items),
        replay_estimate=dict(method="ceil(geometry-passed type count times capped decoded-pilot fraction)",
                             source="Pilot token/call journals; budget and native/call-limit finishes",
                             assumption="Extrapolation from decoded pilot pairs; geometry-refused items have zero decode cost",
                             pilot_samples={name: dict(items=group["sample_items"],
                                                       capped=group["pilot_capped_items"])
                                            for name, group in per_family.items()}),
        budget_time_bound=dict(sampled_slot_limit=sampled_limit, closing_tokens=close_tokens,
                               native_total_token_cap=budget["max_new_tokens"],
                               native_call_limit=budget["max_calls"], hard_wall_clock_bound=False,
                               injected_work_in_observed_seconds_per_callback=True,
                               call_deferral_slots=budget["call_window_tokens"],
                               method="Each item: sampled-slot limit times measured native seconds per "
                                      "sampled token, plus measured non-native overhead. Observed native-tail "
                                      "caps use the total-token limit. No item bound shortens its measured time."),
        method="Three full-query items per type and digested remaining rows; duplicate journal/bundle, "
               "all 84 measured geometry outcomes, zero decode cost for bound refusals, "
               "means of individual time bounds and uncapped times, "
               "explicit zero/replay-estimated/all-capped scenarios, 50 percent margin and a 16 MiB reserve. "
               "Capped mean costs are floored by ordinary mean costs. This is an empirical wall-time projection.")


def validate(evidence, family_sha256, artifact):
    if not isinstance(evidence, dict):
        raise ValueError("A full packet requires authenticated pilot return-size evidence")
    report = evidence.get("report", {})
    if report.get("artifact") != artifact:
        raise ValueError("The full packet artifact differs from its pilot artifact")
    scenario = evidence.get("projection_scenario")
    if scenario not in SCENARIOS:
        raise ValueError("A full packet requires an explicitly selected projection scenario")
    complete, parity, receipt = (evidence.get(key, {}) for key in ("complete", "parity", "receipt"))
    if (report.get("family_sha256") != family_sha256
            or complete.get("family", {}).get("sha256") != family_sha256
            or complete.get("mode") != "pilot" or complete.get("synthetic") is not False
            or complete.get("training_decision_allowed") is not False
            or complete.get("artifact") != report.get("artifact")
            or receipt.get("synthetic") is not False or receipt.get("status") != "COMPLETE"
            or receipt.get("complete") is not True or receipt.get("returncode") != 0
            or not report.get("plan_sha256")
            or report["plan_sha256"] != complete.get("plan_sha256")
            or report["plan_sha256"] != receipt.get("plan_sha256")
            or parity.get("pass") is not True
            or parity.get("p1_gate", {}).get("pass") is not True
            or any(parity.get(name, {}).get("pass") is not True for name in ("P2", "P3"))
            or parity.get("camera_call") is not True or parity.get("call_errors")
            or evidence.get("report_canonical_sha256") != C.canonical(report)):
        raise ValueError("Full projection pilot identity, admission or parity differs")
    projection = project(report, scenario)
    if projection != evidence.get("projection"):
        raise ValueError("The bound full-return projection differs from the pilot measurements")
    if not projection["fits"]:
        raise ValueError("The projected full return or runtime exceeds its admitted limits")
    return projection


def from_return(receipt_path, archive_path, family_sha256, artifact, scenario):
    if scenario not in SCENARIOS:
        raise ValueError("A full packet requires an explicitly selected projection scenario")
    import orchard_results as R
    receipt = C.load(receipt_path)
    R.verify(receipt, archive_path, receipt["plan_sha256"])
    names = ("COMPLETE.json", "native/probe/PILOT_REPORT.json", "native/probe/GPU_PARITY.json")
    raw = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        for name in names:
            entry = archive.getmember(name)
            if entry.size > 2*1024**2:
                raise ValueError("Pilot control evidence exceeds its bound")
            raw[name] = archive.extractfile(entry).read()
    complete, report, parity = (json.loads(raw[name]) for name in names)
    for name in names[1:]:
        if complete.get("receipts", {}).get(name) != hashlib.sha256(raw[name]).hexdigest():
            raise ValueError("The passed pilot does not authenticate its report and parity")
    if report.get("parity", {}).get("sha256") != hashlib.sha256(raw[names[2]]).hexdigest():
        raise ValueError("The pilot report binds different parity bytes")
    evidence = dict(receipt=receipt, complete=complete, report=report, parity=parity,
                    report_canonical_sha256=C.canonical(report), projection_scenario=scenario,
                    projection=project(report, scenario),
                    source_receipt=C.pin(receipt_path), source_archive=C.pin(archive_path))
    validate(evidence, family_sha256, artifact)
    return evidence
