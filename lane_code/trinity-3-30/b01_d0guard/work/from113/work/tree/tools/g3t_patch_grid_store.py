"""G3T feature store on the student's unmerged patch grid (geometry-input-v1, Spatial-MLLM's mlp_add connector).

Derived from the GX store extractor (geo_build x.py 480e25b6, which built fs/9cdefbc2 and fs/68918577): the same frame
checks, the same encoder input (pad to square, 1024, bilinear 518, as the tool harness runs G3T), layer 23's patch
tokens (frame + global attention, 2048) and the same valid-region roi_align (aligned, sampling ratio 2). One change:
each frame is pooled onto the student's unmerged Qwen patch grid (2h, 2w) instead of the merged grid (h, w), so the
connector concatenates the 2x2 cells of both frames of every merged token itself, as Spatial-MLLM does. A row is
float16 [32, 2h, 2w, 2048] with pooling "roi_align_valid_region_aligned_sr2_patch_grid".

  lists    --training NAME=training.json ... --eval-cell NAME=CELL_DIR ... [--map SRC=DST ...] --out DIR
           CPU: the unique ordered 32-frame selections of the training rows (grid from each row's input audit) and of
           the eval cells (frames and grid from each cell's preflight input audits) -> DIR/train_sets.jsonl,
           DIR/eval_sets.jsonl (lists.py 7d421d82's logic, with the inputs as arguments).
  extract  SRC_DIR SETS_JSONL STORE_DIR SHARD NSHARDS [LIMIT]
           GPU: shard SHARD of NSHARDS (sorted by key); rows go to STORE_DIR/m_<SHARD>.jsonl, timings to t_<SHARD>.jsonl.
           A rerun skips the selections its shard already wrote.
  seal     SETS_JSONL STORE_DIR
           CPU: verify every selection has exactly one row whose file, sha256 and shape match, then write
           STORE_DIR/manifest.jsonl (rows sorted by key) and STORE_DIR/RECEIPT.json; pin the manifest's sha256.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time
from pathlib import Path

LAYER = 23
FRAMES = 32
FEATURE_DIM = 2048
REPOSITORY, REVISION = "thatbrguy/g3t", "c55e91a04f1cbbad67359072536351201fd19e8b"
SOURCE_SHA256 = "8223a095c258d8f2a720af8c5821f52ecbed1fe64ae127d4b78b8239354b868d"
POOLING = "roi_align_valid_region_aligned_sr2_patch_grid"
ENCODER = {"name": "g3t", "repository": REPOSITORY, "revision": REVISION, "source_sha256": SOURCE_SHA256,
           "input": "square_pad_1024_bilinear_518", "pooling": POOLING}
INPUT_SIDE, PATCH = 518, 14


def sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 22), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with open(path) as stream:
        return json.load(stream)


def read_lines(path):
    with open(path) as stream:
        return [line for line in stream if line.strip()]


def key(shas):
    if len(shas) != FRAMES:
        raise ValueError("A selection has exactly 32 frames")
    return hashlib.sha256("\n".join(shas).encode()).hexdigest()


def patch_grid(grid_thw):
    """(2h, 2w) = the student's unmerged patch grid of a 32-frame video grid [16, 2h, 2w]."""
    t, height, width = (int(value) for value in grid_thw)
    if t * 2 != FRAMES or height % 2 or width % 2:
        raise ValueError(f"Video grid {grid_thw} is not a 32-frame, 2x2-mergeable grid")
    return height, width


def pool_patch_grid(layer_tokens, coords, grid_thw):
    """Layer patch tokens [32, side * side, D] of the 518-px input -> float32 [32, 2h, 2w, D] on the patch grid.

    coords[:, :4] is each frame's valid (unpadded) region in the 1024-px square, as load_and_preprocess_images_square
    returns it; every output cell averages roi_align's 2 x 2 bilinear samples inside its share of that region."""
    import torch
    from torchvision.ops import roi_align

    frames, patches, channels = layer_tokens.shape
    side = int(round(patches ** 0.5))
    if frames != FRAMES or side * side != patches:
        raise ValueError("unexpected G3T patch-token shape")
    height, width = patch_grid(grid_thw)
    grid = layer_tokens.float().reshape(frames, side, side, channels).permute(0, 3, 1, 2).contiguous()
    box = coords[:, :4].double() * (INPUT_SIDE / 1024)
    boxes = torch.cat((torch.arange(frames, dtype=torch.float64)[:, None], box), 1).float().to(grid.device)
    pooled = roi_align(grid, boxes, output_size=(height, width), spatial_scale=1 / PATCH, sampling_ratio=2, aligned=True)
    return pooled.permute(0, 2, 3, 1).contiguous()


# ---------------------------------------------------------------------------------------------- lists

def remap(path, maps):
    for source, target in maps:
        if path == source or path.startswith(source + "/"):
            return target + path[len(source):]
    if maps:
        raise ValueError("unmapped path " + path)
    return path


def training_sets(name, path, maps, sets):
    payload = read_json((remap(path, maps)))
    audits = payload["input_audits"]
    audits = audits if isinstance(audits, dict) else {audit["qid"]: audit for audit in audits}
    for row in payload["rows"]:
        frames = row["student_input"]["frames"]
        shas = [frame["sha256"] for frame in frames]
        selection = key(shas)
        grid = audits[row["qid"]]["video_grid_thw"][0]
        entry = sets.setdefault(selection, {"key": selection, "frames": shas, "paths": [remap(f["path"], maps) for f in frames],
                                            "grid": grid, "sources": [], "rows": {}})
        if entry["grid"] != grid:
            raise ValueError(f"grid differs within one selection {selection}")
        if name not in entry["sources"]:
            entry["sources"].append(name)
        entry["rows"][name] = entry["rows"].get(name, 0) + 1


def eval_sets(name, cell, maps, sets):
    cell = Path(remap(str(cell), maps))
    preflight = read_json((cell / "preflight/preflight.json"))
    manifest = read_json((remap(preflight["manifest"]["path"], maps)))
    media = read_json((remap(manifest["media"]["path"], maps)))
    if not all(isinstance(value, dict) and "frame_receipt" in value for value in media.values()):
        media = next(value for value in media.values()
                     if isinstance(value, dict) and all(isinstance(item, dict) and "frame_receipt" in item for item in value.values()))
    by_frames = {}
    for video, item in media.items():
        selection = read_json((remap(item["frame_receipt"]["path"], maps)))
        pngs = [frame["png"] for frame in selection["frames"]]
        by_frames[tuple(png["sha256"] for png in pngs)] = (video, [remap(png["path"], maps) for png in pngs])
    for line in read_lines(cell / "preflight/input_audits.jsonl"):
        audit = json.loads(line)
        shas = tuple(audit["frame_hashes"])
        if shas not in by_frames:
            raise ValueError(f"{name} item {audit['qid']}: frame_hashes are not the PNG sha256s of any media receipt")
        video, paths = by_frames[shas]
        selection = key(list(shas))
        grid = audit["video_grid_thw"][0]
        entry = sets.setdefault(selection, {"key": selection, "frames": list(shas), "paths": paths, "grid": grid,
                                            "sources": [], "items": 0, "video_id": video})
        if entry["grid"] != grid:
            raise ValueError(f"grid differs within one eval selection {selection}")
        if name not in entry["sources"]:
            entry["sources"].append(name)
        entry["items"] += 1


def build_lists(training, cells, maps, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    train, evaluation = {}, {}
    for name, path in training:
        training_sets(name, path, maps, train)
    for name, cell in cells:
        eval_sets(name, cell, maps, evaluation)
    overlap = set(train) & set(evaluation)
    if overlap:
        raise ValueError(f"{len(overlap)} selections are in both the training and the eval lists")
    report = {}
    for label, sets in (("train", train), ("eval", evaluation)):
        with open(out / f"{label}_sets.jsonl", "x") as stream:
            for selection in sorted(sets):
                stream.write(json.dumps(sets[selection], sort_keys=True) + "\n")
        report[label] = {"selections": len(sets), "bytes": sum(store_bytes(entry["grid"]) for entry in sets.values())}
    return report


def store_bytes(grid_thw):
    height, width = patch_grid(grid_thw)
    return FRAMES * height * width * FEATURE_DIM * 2 + 128  # float16 cells plus the .npy header


# ---------------------------------------------------------------------------------------------- extract

def load(entry, preprocess):
    started = time.time()
    if key(entry["frames"]) != entry["key"]:
        raise ValueError("set key differs from its frames")
    for path, expected in zip(entry["paths"], entry["frames"]):
        if sha(path) != expected:
            raise ValueError(f"frame sha256 differs: {path}")
    images, coords = preprocess(entry["paths"], 1024)
    return entry, images, coords, time.time() - started


def extract(source, sets_path, store, shard, nshards, limit=None):
    import numpy as np
    import torch
    import torch.nn.functional as F

    sys.path.insert(0, str(source))
    from vggt.models.g3t import G3T
    from vggt.utils.load_fn import load_and_preprocess_images_square

    store = Path(store)
    sets = [json.loads(line) for line in read_lines(sets_path)]
    sets = sorted(sets, key=lambda entry: entry["key"])[shard::nshards]
    if limit:
        sets = sets[:limit]
    out_rows, out_times = store / f"m_{shard}.jsonl", store / f"t_{shard}.jsonl"
    store.mkdir(parents=True, exist_ok=True)
    done = {json.loads(line)["key"] for line in read_lines(out_rows)} if out_rows.exists() else set()
    todo = [entry for entry in sets if entry["key"] not in done]
    print(f"shard {shard}/{nshards}: {len(sets)} sets, {len(done)} done, {len(todo)} to do", flush=True)
    torch.manual_seed(0)
    started = time.time()
    model = G3T.from_pretrained(REPOSITORY, revision=REVISION).eval().to("cuda")
    print(f"model load {time.time() - started:.1f}s", flush=True)
    pool = cf.ThreadPoolExecutor(2)
    futures = [pool.submit(load, entry, load_and_preprocess_images_square) for entry in todo[:2]]
    following = 2
    for _ in range(len(todo)):
        entry, images, coords, load_seconds = futures.pop(0).result()
        if following < len(todo):
            futures.append(pool.submit(load, todo[following], load_and_preprocess_images_square))
            following += 1
        item_started = time.time()
        with torch.inference_mode():
            inputs = F.interpolate(images.to("cuda"), size=(INPUT_SIDE, INPUT_SIDE), mode="bilinear", align_corners=False)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                tokens, start = model.aggregator(inputs[None])
            pooled = pool_patch_grid(tokens[LAYER][0, :, start:, :], coords, entry["grid"])
            array = pooled.to(torch.float16).cpu().numpy()
        del tokens
        if array.shape != (FRAMES, *patch_grid(entry["grid"]), FEATURE_DIM) or not np.isfinite(array).all():
            raise ValueError(f"bad or non-finite features for {entry['key']}")
        gpu_seconds = time.time() - item_started
        relative = Path("f") / entry["key"][:2] / f"{entry['key']}.npy"
        target = store / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f".tmp{os.getpid()}.npy")
        np.save(temporary, array, allow_pickle=False)
        os.replace(temporary, target)
        row = {"key": entry["key"], "frames": entry["frames"], "file": str(relative), "sha256": sha(target),
               "shape": list(array.shape), "dtype": "float16", "layer": LAYER, "encoder": ENCODER}
        with out_rows.open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
        with out_times.open("a") as stream:
            stream.write(json.dumps({"key": entry["key"], "load_s": round(load_seconds, 3), "gpu_s": round(gpu_seconds, 3),
                                     "total_s": round(time.time() - item_started + load_seconds, 3),
                                     "bytes": target.stat().st_size,
                                     "peak_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2)}) + "\n")
    print(f"shard {shard} done in {time.time() - started:.0f}s", flush=True)


# ---------------------------------------------------------------------------------------------- seal

def seal(sets_path, store):
    """manifest.jsonl over every selection of SETS_JSONL, verified; returns the receipt."""
    store = Path(store)
    sets = {entry["key"]: entry for entry in (json.loads(line) for line in read_lines(sets_path))}
    rows = {}
    for path in sorted(store.glob("m_*.jsonl")):
        for line in read_lines(path):
            row = json.loads(line)
            if row["key"] in rows:
                raise ValueError(f"selection {row['key']} has more than one row")
            rows[row["key"]] = row
    if set(rows) != set(sets):
        raise ValueError(f"store rows cover {len(set(rows) & set(sets))} of {len(sets)} selections "
                         f"and {len(set(rows) - set(sets))} foreign keys")
    total = 0
    for selection, row in rows.items():
        expected = [FRAMES, *patch_grid(sets[selection]["grid"]), FEATURE_DIM]
        relative = Path(row["file"])
        if (row["frames"] != sets[selection]["frames"] or key(row["frames"]) != selection or row["shape"] != expected
                or row["dtype"] != "float16" or row["layer"] != LAYER or row["encoder"] != ENCODER
                or relative.is_absolute() or ".." in relative.parts):
            raise ValueError(f"row {selection} differs from its selection, grid or encoder")
        if sha(store / relative) != row["sha256"]:
            raise ValueError(f"feature file {row['file']} differs from its row")
        total += (store / relative).stat().st_size
    manifest = store / "manifest.jsonl"
    with manifest.open("x") as stream:
        for selection in sorted(rows):
            stream.write(json.dumps(rows[selection], sort_keys=True) + "\n")
    receipt = {"schema": "g3t-patch-grid-store-v1", "selections": len(rows), "bytes": total, "encoder": ENCODER,
               "layer": LAYER, "sets": {"path": str(sets_path), "sha256": sha(sets_path)},
               "manifest": {"path": str(manifest), "sha256": sha(manifest)},
               "tool_sha256": sha(Path(__file__))}
    with (store / "RECEIPT.json").open("x") as stream:
        stream.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def pairs(values, what):
    result = []
    for value in values or []:
        name, separator, path = value.partition("=")
        if not separator or not name or not path:
            raise SystemExit(f"{what} takes NAME=PATH, got {value}")
        result.append((name, path))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    lists = sub.add_parser("lists")
    lists.add_argument("--training", action="append", required=True)
    lists.add_argument("--eval-cell", action="append", default=[])
    lists.add_argument("--map", action="append", default=[])
    lists.add_argument("--out", required=True)
    run = sub.add_parser("extract")
    for name in ("source", "sets", "store"):
        run.add_argument(name)
    run.add_argument("shard", type=int)
    run.add_argument("nshards", type=int)
    run.add_argument("limit", type=int, nargs="?")
    sealing = sub.add_parser("seal")
    sealing.add_argument("sets")
    sealing.add_argument("store")
    args = parser.parse_args(argv)
    if args.command == "lists":
        result = build_lists(pairs(args.training, "--training"), pairs(args.eval_cell, "--eval-cell"),
                             pairs(args.map, "--map"), args.out)
    elif args.command == "extract":
        result = extract(args.source, args.sets, args.store, args.shard, args.nshards, args.limit)
    else:
        result = seal(args.sets, args.store)
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
