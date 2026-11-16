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


FAMILY_COUNTS = dict(object_abs_distance=150, room_size_estimation=36,
                     camera_displacement=150, camera_movement_direction=150, camera_rotation=150)
GEOMETRY_CAPTURES = 84
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


def pair_size(pair, grounding, root):
    journal = "".join(json.dumps(row, allow_nan=False)+"\n" for row in pair).encode()
    return dict(journal_raw_bytes=len(journal),
                journal_gzip_bytes=len(gzip.compress(journal, compresslevel=6, mtime=0)),
                grounding=measure([grounding] if grounding.exists() else [], root))


class PilotReport:
    def __init__(self, path, config, cuda):
        self.path, self.cuda = Path(path), cuda
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.value = dict(
            schema="evalx-unscored-native-pilot-report-v1", synthetic=False, complete=False,
            training_decision_allowed=False, full_read_authorized=False,
            family_sha256=config["family"]["sha256"], plan_sha256=config["plan_sha256"],
            artifact=config["worker"]["artifact"], selection=config["worker"]["pilot_selection"],
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
        A.atomic_json(self.path, self.value)
        return self.value


def nonnegative(value):
    if type(value) is not int or value < 0:
        raise ValueError("Pilot byte and file counts must be nonnegative integers")
    return value


def project(report):
    items, geometry = report.get("items", []), report.get("geometry", [])
    selection = report.get("selection", {})
    if (report.get("schema") != "evalx-unscored-native-pilot-report-v1"
            or report.get("synthetic") is not False or report.get("complete") is not True
            or report.get("training_decision_allowed") is not False
            or report.get("full_read_authorized") is not False or report.get("parity_pass") is not True
            or report.get("full_family_counts") != FAMILY_COUNTS
            or report.get("full_geometry_captures") != GEOMETRY_CAPTURES
            or len(items) != 10 or len(geometry) != 5
            or len({row["native"] for row in geometry}) != 5
            or [row["key"] for row in items] != selection.get("item_keys")
            or len(set(selection.get("item_keys", []))) != 10
            or Counter(row["family"] for row in items) != Counter(dict.fromkeys(FAMILY_COUNTS, 2))):
        raise ValueError("Full projection requires a complete passed ten-item/five-capture pilot")
    grouped = defaultdict(list)
    for row in items:
        grouped[row["family"]].append(row)
    compressed = raw = files = 0
    per_family = {}
    for name, count in FAMILY_COUNTS.items():
        sizes = [row["return_size"] for row in grouped[name]]
        journal = max(nonnegative(row["journal_gzip_bytes"]) for row in sizes)
        journal_raw = max(nonnegative(row["journal_raw_bytes"]) for row in sizes)
        grounding = max(nonnegative(row["grounding"]["tar_gzip_bytes"]) for row in sizes)
        grounding_raw = max(nonnegative(row["grounding"]["raw_bytes"]) for row in sizes)
        count_files = max(nonnegative(row["grounding"]["files"]) for row in sizes)
        per_family[name] = dict(items=count, sample_items=len(sizes),
                               maximum_pair_gzip_bytes=journal, maximum_grounding_gzip_bytes=grounding)
        compressed += count*(2*journal+grounding)
        raw += count*(2*journal_raw+grounding_raw)
        files += count*count_files
    compressed += GEOMETRY_CAPTURES*max(nonnegative(row["return_size"]["tar_gzip_bytes"]) for row in geometry)
    raw += GEOMETRY_CAPTURES*max(nonnegative(row["return_size"]["raw_bytes"]) for row in geometry)
    files += GEOMETRY_CAPTURES*max(nonnegative(row["return_size"]["files"]) for row in geometry)
    fixed = report["fixed_return_size"]
    compressed += nonnegative(fixed["tar_gzip_bytes"])
    raw += nonnegative(fixed["raw_bytes"])
    files += nonnegative(fixed["files"])+64
    projected = math.ceil(1.5*compressed)+FIXED_RESERVE
    expanded = math.ceil(1.5*raw)+FIXED_RESERVE
    seconds = (2*report["load_seconds"]+report["parity_seconds"]+
               GEOMETRY_CAPTURES*max(row["seconds"] for row in geometry)+
               sum(count*max(row["seconds"] for row in grouped[name])
                   for name, count in FAMILY_COUNTS.items()))
    if not math.isfinite(seconds) or seconds < 0:
        raise ValueError("Pilot timing projection is not finite and nonnegative")
    return dict(
        schema="evalx-native-full-projection-v1", projected_compressed_bytes=projected,
        projected_expanded_bytes=expanded, projected_files=files,
        compressed_limit=RETURN_LIMIT, expanded_limit=EXPANDED_LIMIT,
        fits=projected <= RETURN_LIMIT and expanded <= EXPANDED_LIMIT and files < 10000,
        per_family=per_family, geometry_captures=GEOMETRY_CAPTURES,
        safety_factor=1.5, fixed_reserve_bytes=FIXED_RESERVE, journal_and_bundle_copies=2,
        full_time_seconds_before_margin=seconds, full_time_seconds_with_margin=math.ceil(1.5*seconds),
        method="Per-family sample maxima, maximum geometry bytes per capture, duplicate journal/bundle, "
               "50 percent growth margin and a 16 MiB control/log reserve; not a worst-case guarantee")


def validate(evidence, family_sha256):
    if not isinstance(evidence, dict):
        raise ValueError("A full packet requires authenticated pilot return-size evidence")
    report = evidence.get("report", {})
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
            or any(parity.get(name, {}).get("pass") is not True for name in ("P1", "P2", "P3"))
            or parity.get("camera_call") is not True or parity.get("call_errors")
            or evidence.get("report_canonical_sha256") != C.canonical(report)):
        raise ValueError("Full projection pilot identity, admission or parity differs")
    projection = project(report)
    if projection != evidence.get("projection"):
        raise ValueError("The bound full-return projection differs from the pilot measurements")
    if not projection["fits"]:
        raise ValueError("The projected full return exceeds its compressed, expanded or file limit")
    return projection


def from_return(receipt_path, archive_path, family_sha256):
    import orchard_results as R
    receipt = C.load(receipt_path)
    R.verify(receipt, archive_path, receipt["plan_sha256"])
    names = ("COMPLETE.json", "native/PILOT_REPORT.json", "native/probe/GPU_PARITY.json")
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
                    report_canonical_sha256=C.canonical(report), projection=project(report),
                    source_receipt=C.pin(receipt_path), source_archive=C.pin(archive_path))
    validate(evidence, family_sha256)
    return evidence
