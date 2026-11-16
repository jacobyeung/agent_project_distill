"""Rows for the head-call arms HC, HX and HA on RG2P2's 396,649 questions (DESIGN_HEADCALL_FULLFT.md section 3).

build (Trinity, CPU): from phase 2's converted exports (phase2-headcall-opus 83c2d47: rung-1 G rows_g_calls and the
  RG2VS motion rows_vs_calls), RG2P2's drop list and the rung-2 parts, write
    HC_SIDECAR.jsonl.gz   kind headcall: one entry per kept head-call row (its calls, template, derived items)
    HX_SIDECAR.jsonl.gz   kind queries: the same rows' depth calls, bound to their answer-only (RG2P2_X) targets
    HA_SIDECAR.jsonl.gz   kind queries: the same rows' depth calls, bound to their RG2P2_A trace targets
    HC_REPLACE.jsonl.gz   HC's targets that differ from RG2P2_X's: head-call traces and plain (counting) G traces
    TABLE.json / TABLE.md the exact per-type table of head-call, fallback, answer-only and plain rows
    BUILD.json            every input's SHA-256 and every output's pin
  HC trains RG2P2_X's rows with HC_REPLACE's targets; HX trains RG2P2_X's rows; HA trains RG2P2_A's rows. All three use
  the same qids, so the trainer gives them the same order (rows are sorted by qid at admission, then shuffled by seed).

subset (Trinity, CPU): the same files restricted to a scene list (the 8-GPU smoke's 20 smoke-bank scenes).

index (code-aws, CPU): rewrite RG2P2_X's frozen candidate_index.jsonl into HC's: each replaced entry becomes an inline
  row (the X twin's own row with its AWS frame paths, target replaced) whose target sits in a shared shard file; every
  other entry is copied byte for byte. Each replaced twin must have the input identity and answer-only target the
  build recorded.
"""
import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import tarfile
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from headcall import rows as R  # noqa: E402
from student_pilot.auxiliary_targets import input_identity  # noqa: E402

DROP_SHA256 = "720e97114726805fe7020d8b3ced80452e6761f7d62288b69551164f41ad7081"  # newline-joined, no final newline
SUPPORT_QID = "h28f71a03e7cd6f45923569e2"
ROOM_COMMIT = "601b3488"
ROUTE_ROWS = 3900
QA_ROWS = 396_649
ANSWER_ONLY = "<think>\n\n</think>\n\n"
MOTION = ("camera_movement_direction", "camera_displacement")
REPLACE_SCHEMA = "headcall-replace-v1"
TARGET_SHARD_BYTES = 64 * 1024 * 1024


def sha_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def jsonl(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def drop_list(path):
    qids = open(path).read().split()
    if hashlib.sha256("\n".join(qids).encode()).hexdigest() != DROP_SHA256:
        raise ValueError("The drop list differs from RG2P2's drop_qids.txt (720e9711)")
    return set(qids)


def g_traces(archives, wanted):
    """{qid: target} of the published G rows (RG2P2_A's T_base targets) for the wanted qids."""
    found = {}
    for archive in archives:
        with tarfile.open(archive, "r:gz") as tar:
            for member in tar:
                if not member.isfile():
                    continue
                row = json.loads(tar.extractfile(member).read())
                if row["qid"] in wanted:
                    found[row["qid"]] = row["target"]
    missing = wanted - set(found)
    if missing:
        raise ValueError(f"{len(missing)} head-call qids have no published G row (first {sorted(missing)[:3]})")
    return found


def twin_entry(entry, target):
    return {"qid": entry["qid"], "dataset": entry["dataset"], "scene": entry["scene"], "kind": "queries", "target_sha256": R.text_sha256(target),
            "input_sha256": entry["input_sha256"], "queries": R.twin_queries(entry["head_calls"])}


def build(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    drop = drop_list(args.drop)
    table = OrderedDict()
    hc, replace, a_targets = [], [], {}

    def count(source, category, route):
        # Keyed by source and type: ADT and rung-1 G share two type names (absolute direction, relative size).
        cell = table.setdefault(f"{source}/{category}", OrderedDict([("source", source), ("type", category), ("rows", 0),
                                                                     ("headcall", 0), ("fallback", 0), ("answer_only", 0),
                                                                     ("plain", 0)]))
        cell["rows"] += 1
        cell[route] += 1

    def keep_headcall(row, x_target):
        entry = {"qid": row["qid"], "dataset": row["dataset"], "scene": row["scene"], "kind": "headcall",
                 "target_sha256": R.text_sha256(row["target"]),
                 "input_sha256": input_identity(row), "head_calls": row["head_calls"],
                 "target_template": row["target_template"], "head_derived": row["head_derived"]}
        hc.append(entry)
        replace.append({"qid": row["qid"], "dataset": row["dataset"], "scene": row["scene"], "category": row["category"],
                        "route": "headcall", "target": row["target"],
                        "input_sha256": entry["input_sha256"], "x_target_sha256": R.text_sha256(x_target)})
        return entry

    # Rung-1 G (T_base / X_base after RG2P2's drops)
    seen_g = 0
    for row in jsonl(args.g_rows):
        route = row["headcall_route"]
        if row["qid"] in drop or route == "support":
            continue
        seen_g += 1
        x_target = ANSWER_ONLY + row["answer"]
        if route == "headcall":
            keep_headcall(row, x_target)
        elif route == "plain":
            replace.append({"qid": row["qid"], "dataset": row["dataset"], "scene": row["scene"], "category": row["category"],
                            "route": "plain", "target": row["target"],
                            "input_sha256": input_identity(row), "x_target_sha256": R.text_sha256(x_target)})
            a_targets[row["qid"]] = row["target"]
        elif row["target"] != x_target:
            raise ValueError(f"A {route} row's target is not its answer-only twin ({row['qid']})")
        count("rung1_G", row["category"], route)
    # RG2VS motion rows (camera movement direction and displacement)
    vs_t = {}
    for entry in jsonl(args.vs_t):
        if entry["question_type"] in MOTION:
            vs_t[entry["qid"]] = entry["target"]
    vs_x = Counter()
    for entry in jsonl(args.vs_x):
        if entry["qid"] in drop:
            raise ValueError("RG2P2 drops no VSTI row")
        if entry["question_type"] not in MOTION:
            count("RG2VS", entry["question_type"], "answer_only")
        vs_x[entry["question_type"]] += 1
    seen_vs = 0
    for row in jsonl(args.vs_rows):
        seen_vs += 1
        x_target = ANSWER_ONLY + row["answer"]
        if row["headcall_route"] == "headcall":
            keep_headcall(row, x_target)
        elif row["target"] != x_target:
            raise ValueError(f"A motion fallback row's target is not its answer-only twin ({row['qid']})")
        count("RG2VS", row["category"], row["headcall_route"])
    if seen_vs != sum(vs_x[c] for c in MOTION):
        raise ValueError("The motion rows differ from RG2VS_X's motion census")
    # ADT (RG2DS after drops), room (RG2RS at RG2RSP's commit) and route rows: answer-only twins in HC
    for entry in jsonl(args.ds_x):
        if entry["qid"] not in drop:
            count("RG2DS", entry["question_type"], "answer_only")
    for entry in jsonl(args.rs_x):
        if entry["generation_commit"].startswith(ROOM_COMMIT):
            count("RG2RSP", entry["question_type"], "answer_only")
    route_manifest = json.load(open(args.route_manifest))
    if route_manifest["counts"]["unique_route_questions"] != ROUTE_ROWS:
        raise ValueError("The route manifest is not RG2P2's 3,900 route rows")
    table["RG2RT2/route_planning"] = OrderedDict([("source", "RG2RT2"), ("type", "route_planning"), ("rows", ROUTE_ROWS),
                                                  ("headcall", 0), ("fallback", 0), ("answer_only", ROUTE_ROWS), ("plain", 0)])
    table = OrderedDict(sorted(table.items()))
    total = sum(cell["rows"] for cell in table.values())
    if total != QA_ROWS:
        raise ValueError(f"The arms' rows sum to {total}, not RG2P2's {QA_ROWS}")
    # Twins: HX binds to the answer-only targets, HA to RG2P2_A's traces.
    hc_qids = {entry["qid"] for entry in hc}
    g_wanted = hc_qids - set(vs_t)
    a_targets.update(g_traces(sorted(Path(args.g_archives).glob("rows_g_*.tar.gz")), g_wanted))
    a_targets.update({qid: target for qid, target in vs_t.items() if qid in hc_qids})
    for item in replace:
        if item["route"] == "plain" and a_targets[item["qid"]] != item["target"]:
            raise ValueError("A plain row's G target differs from its published G row")
    x_targets = {item["qid"]: item["x_target_sha256"] for item in replace}
    hx = [dict(twin_entry(entry, ""), target_sha256=x_targets[entry["qid"]]) for entry in hc]
    ha = [twin_entry(entry, a_targets[entry["qid"]]) for entry in hc]
    source = {"phase2_commit": "83c2d47", "g_rows": sha_file(args.g_rows), "vs_rows": sha_file(args.vs_rows),
              "drop_qids": DROP_SHA256}
    pins = {arm: R.write_sidecar(out / f"{arm}_SIDECAR.jsonl.gz", arm, entries, source)
            for arm, entries in (("HC", hc), ("HX", hx), ("HA", ha))}
    write_replace(out / "HC_REPLACE.jsonl.gz", replace, source)
    totals = OrderedDict((key, sum(cell[key] for cell in table.values()))
                         for key in ("rows", "headcall", "fallback", "answer_only", "plain"))
    result = OrderedDict([("schema", "headcall-rows-build-v1"), ("table", table), ("totals", totals),
                          ("queried_depth_points", sum(len(R.twin_queries(entry["head_calls"])) for entry in hc)),
                          ("head_calls", sum(len(entry["head_calls"]) for entry in hc)),
                          ("counts", {"g_rows_kept": seen_g, "motion_rows": seen_vs, "replaced_targets": len(replace)})])
    (out / "TABLE.json").write_text(json.dumps(result, indent=1) + "\n")
    (out / "TABLE.md").write_text(table_markdown(table, totals))
    inputs = {name: {"path": str(Path(getattr(args, name)).resolve()), "sha256": sha_file(getattr(args, name))}
              for name in ("g_rows", "vs_rows", "vs_t", "vs_x", "ds_x", "rs_x", "drop", "route_manifest")}
    inputs["g_archives"] = {path.name: sha_file(path) for path in sorted(Path(args.g_archives).glob("rows_g_*.tar.gz"))}
    outputs = {**{f"{arm}_SIDECAR": pin for arm, pin in pins.items()},
               "HC_REPLACE": {"path": str(out / "HC_REPLACE.jsonl.gz"), "sha256": sha_file(out / "HC_REPLACE.jsonl.gz")},
               "TABLE": {"path": str(out / "TABLE.json"), "sha256": sha_file(out / "TABLE.json")}}
    (out / "BUILD.json").write_text(json.dumps({"schema": "headcall-rows-build-v1", "inputs": inputs, "outputs": outputs,
                                                "code_sha256": sha_file(__file__)}, indent=1) + "\n")
    print(json.dumps({"totals": totals, "outputs": {k: v["sha256"][:12] for k, v in outputs.items()}}))


def table_markdown(table, totals):
    lines = ["| Type | Source | Rows | Head-call | Fallback | Answer-only | Plain |", "|---|---|---:|---:|---:|---:|---:|"]
    for cell in table.values():
        lines.append(f"| {cell['type']} | {cell['source']} | {cell['rows']:,} | {cell['headcall']:,} | {cell['fallback']:,} | "
                     f"{cell['answer_only']:,} | {cell['plain']:,} |")
    lines.append(f"| **Total** | | **{totals['rows']:,}** | **{totals['headcall']:,}** | **{totals['fallback']:,}** | "
                 f"**{totals['answer_only']:,}** | **{totals['plain']:,}** |")
    return "\n".join(lines) + "\n"


def write_replace(path, items, source):
    """Deterministic gzip JSONL of HC's replaced targets, sorted by qid."""
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", mtime=0) as stream:
        stream.write((json.dumps({"schema": REPLACE_SCHEMA, "entries": len(items), "source": source},
                                 sort_keys=True) + "\n").encode())
        for item in sorted(items, key=lambda value: value["qid"]):
            stream.write((json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n").encode())
    with open(path, "xb") as handle:
        handle.write(buffer.getvalue())


def read_replace(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        header = json.loads(stream.readline())
        items = [json.loads(line) for line in stream if line.strip()]
    if header.get("schema") != REPLACE_SCHEMA or header.get("entries") != len(items):
        raise ValueError("Not a complete HC replacement file")
    return {item["qid"]: item for item in items}


def index(args):
    """RG2P2_X's candidate index -> HC's (inline rows with sharded targets for the replaced entries)."""
    replace = read_replace(args.replace)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    shard_index, shard_size, shard = 0, 0, None
    shards, done, counts = [], set(), Counter()

    def open_shard():
        nonlocal shard_index, shard_size, shard
        if shard is not None:
            shard.close()
        path = out / f"targets_{shard_index:03d}.txt"
        shard_index, shard_size = shard_index + 1, 0
        shard = open(path, "xb")
        shards.append(path)
        return path

    path = open_shard()
    with open(args.x_index, "rb") as source, open(out / "candidate_index.jsonl", "xb") as target:
        for line in source:
            entry = json.loads(line)
            item = replace.get(entry["qid"])
            if item is None:
                target.write(line)
                counts["copied"] += 1
                continue
            if "student_input" in entry:
                row = entry
            else:
                payload = Path(entry["row_path"]).read_bytes()
                if hashlib.sha256(payload).hexdigest() != entry["row_sha256"]:
                    raise ValueError(f"X row file differs from its index pin ({entry['qid']})")
                row = json.loads(payload)
            if (row["qid"] != entry["qid"] or row["category"] != item["category"] or input_identity(row) != item["input_sha256"]
                    or R.text_sha256(row["target"]) != item["x_target_sha256"]):
                raise ValueError(f"The X twin differs from the build's record ({entry['qid']})")
            data = item["target"].encode("utf-8")
            if shard_size + len(data) > TARGET_SHARD_BYTES:
                path = open_shard()
            offset = shard_size
            shard.write(data)
            shard_size += len(data)
            new = {key: value for key, value in entry.items()
                   if key not in ("row_path", "row_sha256", "target_path", "sha256", "target_offset", "target_length")}
            new.update(category=row["category"], dataset=row["dataset"], scene=row["scene"], student_input=row["student_input"],
                       target=item["target"], target_path=str(Path(args.shard_root or out) / path.name),
                       target_offset=offset, target_length=len(data), sha256=hashlib.sha256(data).hexdigest())
            for key in ("provisional_diagnostic", "generation_commit", "validation_commit"):
                if key in row and key not in new:
                    new[key] = row[key]
            target.write((json.dumps(new, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode())
            done.add(entry["qid"])
            counts["replaced_" + item["route"]] += 1
    shard.close()
    missing = set(replace) - done
    if missing:
        raise ValueError(f"{len(missing)} replacement qids are absent from the X index (first {sorted(missing)[:3]})")
    manifest = {"schema": "headcall-hc-index-v1", "x_index": {"path": str(Path(args.x_index).resolve()),
                                                              "sha256": sha_file(args.x_index)},
                "replace": {"path": str(Path(args.replace).resolve()), "sha256": sha_file(args.replace)},
                "candidate_index": {"sha256": sha_file(out / "candidate_index.jsonl")},
                "target_shards": {p.name: sha_file(p) for p in shards}, "counts": dict(counts)}
    (out / "HC_INDEX.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    print(json.dumps(manifest["counts"]))


def subset(args):
    """The smoke's sidecars and replacements: every entry whose (dataset, scene) is on the scene list."""
    scenes = {tuple(item) for item in json.load(open(args.scenes))}
    source, out = Path(args.build), Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    pins, counts = {}, {}
    for arm in ("HC", "HX", "HA"):
        header, entries = R.read_sidecar(source / f"{arm}_SIDECAR.jsonl.gz")
        kept = [entry for entry in entries if (entry["dataset"], entry["scene"]) in scenes]
        pins[arm] = R.write_sidecar(out / f"{arm}_SIDECAR.jsonl.gz", arm, kept,
                                    {**header["source"], "subset_scenes": sha_file(args.scenes)})
        counts[arm] = len(kept)
    replace = [item for item in read_replace(source / "HC_REPLACE.jsonl.gz").values()
               if (item["dataset"], item["scene"]) in scenes]
    write_replace(out / "HC_REPLACE.jsonl.gz", replace, {"subset_scenes": sha_file(args.scenes)})
    counts["HC_REPLACE"] = len(replace)
    pins["HC_REPLACE"] = {"path": str(out / "HC_REPLACE.jsonl.gz"), "sha256": sha_file(out / "HC_REPLACE.jsonl.gz")}
    (out / "SUBSET.json").write_text(json.dumps({"schema": "headcall-rows-subset-v1", "scenes": sorted(scenes),
                                                 "counts": counts, "outputs": pins}, indent=1) + "\n")
    print(json.dumps(counts))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    for name in ("g-rows", "vs-rows", "vs-t", "vs-x", "ds-x", "rs-x", "drop", "route-manifest", "g-archives", "out"):
        b.add_argument("--" + name, required=True)
    i = sub.add_parser("index")
    i.add_argument("--x-index", required=True)
    i.add_argument("--replace", required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--shard-root", help="the directory the shards are read from at admission (default --out)")
    u = sub.add_parser("subset")
    u.add_argument("--build", required=True, help="a build output directory")
    u.add_argument("--scenes", required=True, help="JSON [[dataset, scene], ...]")
    u.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    {"build": build, "index": index, "subset": subset}[args.command](args)


if __name__ == "__main__":
    main()
