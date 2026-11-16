import copy
import hashlib
import json
from pathlib import Path


def nested_indices(total, sparse, count=64):
    if (type(total) is not int or total < count or len(sparse) != 32
            or sparse != sorted(set(sparse)) or sparse[0] != 0 or sparse[-1] >= total):
        raise ValueError("Dense evaluation requires 32 ordered original views and at least 64 source frames")
    chosen = set(sparse)
    while len(chosen) < count:
        ordered = sorted(chosen)
        intervals = [(b-a, a, b) for a, b in zip(ordered, ordered[1:] + [total])]
        length, left, right = max(intervals, key=lambda value: (value[0], -value[1]))
        if length < 2:
            raise ValueError("The original clip cannot supply distinct nested dense frames")
        chosen.add(min(total-1, (left+right)//2))
    return sorted(chosen)


def attach_dense(row, dense, settings, verify=True):
    from .gf1 import dense_inputs
    from .r2_frames import verify_frame
    result = copy.deepcopy(row)
    result["student_input"]["geometry_dense"] = copy.deepcopy(dense)
    admitted, positions = dense_inputs(result, settings)
    n = settings["dense_frames"]
    if (len(admitted["timestamps"]) != n or admitted["fps"] <= 0
            or admitted["total_num_frames"] <= admitted["frame_indices"][-1]
            or any(abs(t-i/admitted["fps"]) > 1e-6 for i, t in
                   zip(admitted["frame_indices"], admitted["timestamps"], strict=True))):
        raise ValueError("Dense evaluation timestamps or source bounds differ")
    if verify:
        for frame in {value["path"]: value for value in admitted["frames"]}.values():
            verify_frame(frame)
    return result, positions


def decode_dense(video_pin, sparse, settings, destination):
    import av
    from .p3_provenance import file_pin, pinned
    from .r2_frames import verify_frame
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    wanted = nested_indices(sparse["total_num_frames"], sparse["frame_indices"], settings["dense_frames"])
    existing = dict(zip(sparse["frame_indices"], sparse["frames"], strict=True))
    frames, fps = {}, sparse["fps"]
    with av.open(str(pinned(video_pin))) as container:
        stream = container.streams.video[0]
        if abs(float(stream.average_rate)-fps) > 1e-6:
            raise ValueError("Dense and student FPS differ")
        for index, frame in enumerate(container.decode(stream)):
            if index not in wanted:
                continue
            if index in existing:
                verify_frame(existing[index])
                frames[index] = existing[index]
            else:
                path = destination / f"frame_{index:08d}.png"
                frame.to_image().save(path)
                frames[index] = file_pin(path)
            if len(frames) == len(wanted):
                break
    if set(frames) != set(wanted):
        raise ValueError("Video decode did not cover the frozen dense membership")
    return dict(frames=[frames[index] for index in wanted], frame_indices=wanted,
                timestamps=[index/fps for index in wanted], fps=fps,
                total_num_frames=sparse["total_num_frames"])


def prepare_membership(rows, dense_by_clip, settings, output, shuffle=None):
    """shuffle: None for the true read, or dict(seed=int[, grids=..., require_same_grid=bool]) for the
    shuffled-bank baseline: every clip reads another clip's geometry bank (gf1_cache.shuffle_rows)."""
    from .p3_provenance import write, file_pin
    selected, identities = [], set()
    for row in rows:
        identity = str(row.get("qid", row.get("id")))
        if identity in identities or identity == "None":
            raise ValueError("Benchmark membership must contain unique explicit item identities")
        identities.add(identity)
        clip = row["student_input"].get("clip_id", row.get("video_id"))
        if clip not in dense_by_clip:
            raise ValueError(f"Dense evaluation lacks clip {clip}; the denominator cannot shrink")
        value, _ = attach_dense(row, dense_by_clip[clip], settings)
        selected.append(value)
    if not selected:
        raise ValueError("Dense benchmark membership is empty")
    plan = None
    if shuffle is not None:
        from .gf1_cache import shuffle_rows
        if not isinstance(shuffle, dict) or set(shuffle) - {"seed", "grids", "require_same_grid"}:
            raise ValueError("Shuffled-bank option takes seed, grids and require_same_grid")
        selected, plan = shuffle_rows(selected, settings, **shuffle)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    path = output / "rows.jsonl"
    with path.open("x") as handle:
        for row in selected:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    receipt = dict(schema="dense-evaluation-v1", count=len(selected), dense_count=len(selected),
                   dense_frames=settings["dense_frames"], student_frames=32, rows=file_pin(path),
                   membership_sha256=hashlib.sha256("\n".join(sorted(identities)).encode()).hexdigest())
    if plan is not None:
        write(output / "bank_permutation.json", plan)
        receipt["shuffled_bank"] = dict(seed=plan["seed"], permutation_sha256=plan["permutation_sha256"],
                                        counts=plan["counts"], plan=file_pin(output / "bank_permutation.json"))
    write(output / "receipt.json", receipt)
    return receipt
