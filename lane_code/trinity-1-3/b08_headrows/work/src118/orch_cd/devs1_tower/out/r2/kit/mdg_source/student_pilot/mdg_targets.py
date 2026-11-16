"""Union-mask targets, embedding confusers and retained RGB negative audits."""
import argparse
import csv
from dataclasses import dataclass, field
import json
import math
from pathlib import Path

import numpy as np

from .grounding_targets import (MIN_VIS, SHAPE, STRUCTURAL, _hash, _label, _raster,
                                _visible, build_index, eval_masks, in_mask)


@dataclass
class MDGUnits:
    scene: str
    qid: str
    labels: list[str]
    kind: list[str]
    frame_presence: np.ndarray
    clip_present: np.ndarray
    unique: np.ndarray
    masks: np.ndarray
    used: np.ndarray
    _inst: np.ndarray = field(default=None, repr=False)
    _label_ids: dict = field(default_factory=dict, repr=False)
    _rgb_wh: tuple = (320, 240)


def _vocabulary(vocab):
    return {v for v in map(_label, vocab) if v and not STRUCTURAL.search(v)}


def mdg_units_for_clip(npz_or_row, vocab, confusers, *, max_visible=24, absent_share=.30,
                       confuser_share=.5, seed_key):
    if (int(max_visible) != max_visible or max_visible < 0 or not 0 <= absent_share < 1
            or not 0 <= confuser_share <= 1):
        raise ValueError('Invalid visible limit or negative share')
    max_visible = int(max_visible)
    scene, qid, inst, used, aggregation, rgb_wh = _raster(npz_or_row)
    by_label, counts, visible = _visible(inst, used, aggregation)
    visible = sorted(visible, key=lambda v: (_hash(f'{qid}|{v}'), v))[:max_visible]
    forbidden = set(aggregation.values())
    n_absent = math.ceil(absent_share / (1 - absent_share) * len(visible))
    candidates = _vocabulary(c for v in visible for c in confusers.get(v, [])) - forbidden
    confusing = sorted(candidates, key=lambda v: (_hash(f'{seed_key}|c|{v}'), v))[
        :round(confuser_share * n_absent)]
    absent = _vocabulary(vocab) - forbidden - set(confusing)
    absent = sorted(absent, key=lambda v: (_hash(f'{seed_key}|{v}'), v))[:n_absent - len(confusing)]
    labels = visible + confusing + absent
    presence = np.full((len(labels), SHAPE[0]), np.nan, np.float32)
    masks = np.zeros((len(labels), *SHAPE), bool)
    for q, label in enumerate(labels):
        ids = by_label.get(label, [])
        for f in np.flatnonzero(used):
            area = max((counts[f].get(i, 0) for i in ids), default=0)
            if not area:
                presence[q, f] = 0
            else:
                if area / (SHAPE[1] * SHAPE[2]) >= MIN_VIS:
                    presence[q, f] = 1
                masks[q, f] = np.isin(inst[f], ids)
    present = np.zeros(len(labels), np.float32)
    present[:len(visible)] = 1
    unique = np.array([len(by_label.get(v, [])) == 1 for v in labels], dtype=bool)
    return MDGUnits(scene, qid, labels,
                    ['visible'] * len(visible) + ['confuser'] * len(confusing) + ['scene_absent'] * len(absent),
                    presence, present, unique, masks, used, inst, dict(by_label), rgb_wh)


def to_tensors(units):
    import torch
    valid = np.isfinite(units.frame_presence) & (units.clip_present[:, None] == 1)
    return dict(frame_presence=torch.from_numpy(np.nan_to_num(units.frame_presence)),
                frame_valid=torch.from_numpy(valid), clip_present=torch.from_numpy(units.clip_present),
                masks=torch.from_numpy(units.masks), mask_valid=torch.from_numpy(units.frame_presence == 1))


def build_confusers(vocab, embed, *, k=10):
    if int(k) != k or k < 0:
        raise ValueError('Confuser count must be a nonnegative integer')
    k = int(k)
    labels = sorted(_vocabulary(vocab))
    vectors = []
    for label in labels:
        value = embed(label)
        if hasattr(value, 'detach'):
            value = value.detach().cpu().float().numpy()
        value = np.asarray(value, dtype=np.float64)
        if value.ndim != 1 or not value.size or not np.isfinite(value).all() or not np.linalg.norm(value):
            raise ValueError(f'Expected a finite nonzero embedding vector for {label!r}')
        if vectors and value.shape != vectors[0].shape:
            raise ValueError('Label embedding dimensions differ')
        vectors.append(value / np.linalg.norm(value))
    if not labels:
        return {}
    matrix = np.stack(vectors)
    result = {}
    for i, label in enumerate(labels):
        scores = matrix @ matrix[i]
        order = sorted((j for j in range(len(labels)) if j != i), key=lambda j: (-scores[j], labels[j]))
        result[label] = [labels[j] for j in order[:k]]
    return result


def label_embedder(safetensors_path, tensor_name, tokenizer):
    import torch
    from safetensors import safe_open
    if isinstance(tokenizer, (str, Path)):
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(tokenizer), local_files_only=True, trust_remote_code=False)
    with safe_open(str(safetensors_path), framework='pt', device='cpu') as handle:
        weight = handle.get_tensor(tensor_name)
    if weight.ndim != 2 or not weight.is_floating_point():
        raise ValueError('Expected a floating-point input-embedding matrix')

    def embed(label):
        ids = tokenizer.encode(label, add_special_tokens=False)
        if not ids or any(i < 0 or i >= weight.shape[0] for i in ids):
            raise ValueError('Label tokenization is empty or outside the embedding matrix')
        with torch.no_grad():
            value = weight[ids].float().mean(0)
        if not torch.isfinite(value).all():
            raise ValueError('Label embedding is nonfinite')
        return value.numpy()
    return embed


def _load_index(paths):
    if len(paths) == 1 and Path(paths[0]).suffix == '.json':
        value = json.loads(Path(paths[0]).read_text())
        if isinstance(value, dict):
            return value
        paths = value
    return build_index(paths, exclude_scenes=[])


def _sheet(clip, used, label, kind, frame_root, destination):
    from PIL import Image, ImageDraw
    from .grounding_train import clip_row
    frames = clip_row(clip)['student_input']['frames']
    chosen = np.flatnonzero(used)
    if len(chosen) < 4:
        raise ValueError('Negative audit requires four used RGB frames')
    chosen = chosen[np.linspace(0, len(chosen) - 1, 4, dtype=int)]
    sheet = Image.new('RGB', (640, 528), 'white')
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 6), f'{kind}: {label}', fill='black')
    for slot, f in enumerate(chosen):
        frame = frames[f]
        source = Path(frame_root) / Path(frame['path']).relative_to('/data2')
        if _hash_bytes(source) != frame['sha256']:
            raise ValueError(f'RGB SHA256 differs: {source}')
        with Image.open(source) as image:
            image = image.convert('RGB')
            image.thumbnail((320, 240))
            x, y = (slot % 2) * 320, 32 + (slot // 2) * 248
            sheet.paste(image, (x, y))
            draw.text((x + 4, y + 226), f'frame {f}', fill='white', stroke_width=1, stroke_fill='black')
    with destination.open('xb') as stream:
        sheet.save(stream, format='PNG')


def _hash_bytes(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(clips_jsonl, confusers, *, frame_root, out, n=40):
    if int(n) != n or n < 0:
        raise ValueError('Audit count must be a nonnegative integer')
    n = int(n)
    index = build_index(clips_jsonl, exclude_scenes=[])
    clips = sorted(index['train'] + index['val'], key=lambda r: (_hash(f'{r["scene"]}|{r["qid"]}'), r['qid']))
    selected = {'scene_absent': [], 'confuser': []}
    for clip in clips:
        units = mdg_units_for_clip(clip, confusers, confusers, seed_key=f'17|{clip["qid"]}')
        for label, kind in zip(units.labels, units.kind):
            if kind in selected and len(selected[kind]) < n:
                selected[kind].append((clip, label, units.used.copy()))
        if all(len(rows) == n for rows in selected.values()):
            break
    if any(len(rows) < n for rows in selected.values()):
        raise ValueError(f'Insufficient audit negatives: {dict((k, len(v)) for k, v in selected.items())}; need {n} each')
    output = Path(out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    with (output / 'AUDIT.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['clip', 'scene', 'label', 'kind', 'sheet_path'])
        writer.writeheader()
        for kind, rows in selected.items():
            for i, (clip, label, used) in enumerate(rows):
                path = output / f'{kind}_{i:03d}.png'
                _sheet(clip, used, label, kind, frame_root, path)
                record = dict(clip=str(clip['qid']), scene=clip['scene'], label=label, kind=kind, sheet_path=str(path))
                writer.writerow(record)
                reports.append(record)
    return reports


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    conf = commands.add_parser('confusers')
    conf.add_argument('--index', nargs='+', required=True)
    conf.add_argument('--embed', required=True)
    conf.add_argument('--tokenizer', required=True)
    conf.add_argument('--out', required=True)
    conf.add_argument('--k', type=int, default=10)
    check = commands.add_parser('audit')
    check.add_argument('--clips-jsonl', nargs='+', required=True)
    check.add_argument('--confusers', required=True)
    check.add_argument('--frame-root', required=True)
    check.add_argument('--n', type=int, default=40)
    check.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    if args.command == 'confusers':
        path, tensor = args.embed.rsplit(':', 1)
        index = _load_index(args.index)
        table = build_confusers(index['vocab'], label_embedder(path, tensor, args.tokenizer), k=args.k)
        with Path(args.out).open('x') as stream:
            json.dump(table, stream, indent=2, sort_keys=True)
            stream.write('\n')
    else:
        audit(args.clips_jsonl, json.loads(Path(args.confusers).read_text()), frame_root=args.frame_root,
              out=args.out, n=args.n)


if __name__ == '__main__':
    main()
