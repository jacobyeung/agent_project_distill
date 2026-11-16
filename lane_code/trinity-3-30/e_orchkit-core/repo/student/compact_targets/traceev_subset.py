import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import subprocess


PRIMARY_WEIGHTS = {'traceev_count_list': 4, 'traceev_abs_distance': 3, 'traceev_size': 3}
PRIMARY_KINDS = tuple(PRIMARY_WEIGHTS)
FRAME_KINDS = ('traceev_frames_all', 'traceev_frames_first', 'traceev_frames_some')
KINDS = PRIMARY_KINDS + FRAME_KINDS + ('traceev_rel_quadrant',)
SUPPORTED_TYPES = ('object_counting', 'object_abs_distance', 'object_size_estimation',
                   'obj_appearance_order', 'grounding', 'object_rel_direction_hard', 'room_size_estimation')
MAX_ROWS = 25000
SEED = 20260925


@dataclass(frozen=True)
class Entry:
    line: int
    offset: int
    length: int
    sha256: str
    qid: str
    kind: str
    scene: tuple[str, str]
    supports: tuple[str, ...]
    disagreement: bool


def priority_quotas(available, budget):
    capacities = {kind: available.get(kind, 0) for kind in PRIMARY_KINDS}
    if budget < 0 or any(value < 0 for value in capacities.values()):
        raise ValueError('negative_quota_capacity')
    quotas = dict.fromkeys(PRIMARY_KINDS, 0)
    remaining = min(budget, sum(capacities.values()))
    active = [kind for kind in PRIMARY_KINDS if capacities[kind]]
    while remaining:
        weight = sum(PRIMARY_WEIGHTS[kind] for kind in active)
        shares = {kind: remaining * PRIMARY_WEIGHTS[kind] // weight for kind in active}
        saturated = [kind for kind in active if shares[kind] >= capacities[kind]]
        if saturated:
            for kind in saturated:
                quotas[kind] = capacities[kind]
                remaining -= capacities[kind]
                active.remove(kind)
            continue
        order = sorted(active, key=lambda kind: (-(remaining * PRIMARY_WEIGHTS[kind] % weight),
                                                 PRIMARY_KINDS.index(kind)))
        for kind in active:
            quotas[kind] = shares[kind]
        for kind in order[:remaining - sum(shares.values())]:
            quotas[kind] += 1
        break
    return quotas


def round_robin(entries, rng):
    scenes = defaultdict(list)
    for entry in entries:
        scenes[entry.scene].append(entry)
    order = sorted(scenes)
    rng.shuffle(order)
    queues = deque()
    for scene in order:
        rng.shuffle(scenes[scene])
        queues.append(scenes[scene])
    while queues:
        queue = queues.popleft()
        yield queue.pop()
        if queue:
            queues.append(queue)


def select_entries(entries, max_rows=MAX_ROWS, seed=SEED):
    if not isinstance(max_rows, int) or isinstance(max_rows, bool) or not 0 < max_rows <= MAX_ROWS:
        raise ValueError(f'max_rows_must_be_between_1_and_{MAX_ROWS}')
    grouped = {kind: [] for kind in KINDS}
    for entry in entries:
        grouped[entry.kind].append(entry)
    orders = {}
    for kind, rows in grouped.items():
        rng = random.Random(f'{seed}:{kind}')
        if kind == 'traceev_count_list':
            orders[kind] = list(round_robin([row for row in rows if row.disagreement], rng))
            orders[kind] += list(round_robin([row for row in rows if not row.disagreement], rng))
        else:
            orders[kind] = list(round_robin(rows, rng))
    available = {kind: len(rows) for kind, rows in orders.items()}
    total = min(max_rows, len(entries))
    attempts = []
    while True:
        scene_limit = total // 100
        selected, scenes, positions = [], Counter(), Counter()
        quotas = priority_quotas(available, total)

        def take(kind, amount):
            before = len(selected)
            rows = orders[kind]
            while positions[kind] < len(rows) and len(selected) - before < amount and len(selected) < total:
                entry = rows[positions[kind]]
                positions[kind] += 1
                if scenes[entry.scene] < scene_limit:
                    selected.append(entry)
                    scenes[entry.scene] += 1
            return len(selected) - before

        if scene_limit:
            for kind in PRIMARY_KINDS:
                take(kind, quotas[kind])
            for kind in PRIMARY_KINDS:
                take(kind, total - len(selected))
            frames = 0
            for kind in FRAME_KINDS:
                frames += take(kind, total // 5 - frames)
            take('traceev_rel_quadrant', total // 10)
        attempts.append({'target': total, 'selected': len(selected), 'scene_limit': scene_limit,
                         'frame_limit': total // 5, 'quadrant_limit': total // 10,
                         'priority_quotas': quotas})
        if len(selected) == total:
            return sorted(selected, key=lambda entry: entry.line), attempts
        total = len(selected)


def read_entries(path):
    entries, offset, digest = [], 0, hashlib.sha256()
    with Path(path).open('rb') as stream:
        for number, line in enumerate(stream, 1):
            digest.update(line)
            try:
                row = json.loads(line)
            except (ValueError, UnicodeDecodeError) as exc:
                raise ValueError(f'invalid_json_at_line_{number}') from exc
            if not isinstance(row, dict) or row.get('question_type') not in KINDS:
                raise ValueError(f'unknown_evidence_kind_at_line_{number}')
            if any(not isinstance(row.get(key), str) or not row[key].strip() for key in ('qid', 'dataset', 'scene')):
                raise ValueError(f'invalid_row_identity_at_line_{number}')
            supports = row.get('supports')
            if isinstance(supports, str):
                supports = [supports]
            if (not isinstance(supports, list) or not supports or
                    any(not isinstance(value, str) or not value.strip() for value in supports) or
                    len(set(supports)) != len(supports)):
                raise ValueError(f'invalid_supports_at_line_{number}')
            check = row.get('label_check')
            if check is not None and not isinstance(check, dict):
                raise ValueError(f'invalid_label_check_at_line_{number}')
            entries.append(Entry(number, offset, len(line), hashlib.sha256(line).hexdigest(), row['qid'],
                row['question_type'], (row['dataset'], row['scene']), tuple(supports),
                row['question_type'] == 'traceev_count_list' and (check or {}).get('agree') is False))
            offset += len(line)
    return entries, digest.hexdigest()


def scene_summary(entries):
    counts = Counter(entry.scene for entry in entries)
    maximum = max(counts.values(), default=0)
    return {'count': len(counts), 'max_rows': maximum, 'max_share': maximum / len(entries) if entries else 0.,
            'per_scene': {'/'.join(scene): {'rows': count, 'share': count / len(entries)}
                          for scene, count in sorted(counts.items())}}


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode()


def select_file(evidence, out, max_rows=MAX_ROWS, seed=SEED):
    evidence, out = Path(evidence).resolve(), Path(out).resolve()
    index_path = Path(str(out) + '.INDEX.jsonl')
    selection_path = Path(str(out) + '.SELECTION.json')
    outputs = (out, index_path, selection_path)
    if evidence in outputs:
        raise ValueError('input_output_alias')
    for path in outputs:
        if path.exists():
            raise FileExistsError(f'output_exists: {path}')
    entries, input_sha = read_entries(evidence)
    selected, attempts = select_entries(entries, max_rows, seed)
    selected_by_line = {entry.line: entry for entry in selected}
    output_digest, index_digest, copied_input_digest = (hashlib.sha256() for _ in range(3))
    out.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with evidence.open('rb') as source, out.open('xb') as destination, index_path.open('xb') as index:
        for number, line in enumerate(source, 1):
            copied_input_digest.update(line)
            entry = selected_by_line.get(number)
            if entry is None:
                continue
            destination.write(line)
            output_digest.update(line)
            written += 1
            record = {'output_line': written, 'input_line': number, 'input_offset': entry.offset,
                      'input_bytes': entry.length, 'sha256': entry.sha256, 'qid': entry.qid,
                      'question_type': entry.kind, 'dataset': entry.scene[0], 'scene': entry.scene[1],
                      'supports': entry.supports, 'label_check_disagreement': entry.disagreement}
            payload = json_bytes(record)
            index.write(payload)
            index_digest.update(payload)
    if copied_input_digest.hexdigest() != input_sha or written != len(selected):
        raise ValueError('input_changed_during_selection; partial_outputs_retained_without_success_manifest')
    before_kind, after_kind = (Counter(entry.kind for entry in rows) for rows in (entries, selected))
    before_support, after_support = (Counter(value for entry in rows for value in entry.supports)
                                    for rows in (entries, selected))
    supported = sorted(set(SUPPORTED_TYPES) | set(before_support))
    parameters = {'max_rows': max_rows, 'seed': seed, 'priority': list(KINDS),
                  'primary_weights': PRIMARY_WEIGHTS, 'frame_max_share': .2,
                  'quadrant_max_share': .1, 'scene_max_share': .01, 'scene_identity': ['dataset', 'scene'],
                  'within_kind': 'seeded scene round-robin; corrected counting rows first',
                  'quota_rounding': 'largest remainder; priority order breaks ties',
                  'leftover_order': list(PRIMARY_KINDS), 'output_order': 'input line order'}
    module = Path(__file__).resolve()
    commit = subprocess.check_output(['git', '-C', str(module.parents[2]), 'rev-parse', 'HEAD'],
                                     text=True, timeout=30).strip()
    report = {'schema': 'traceev-subset-selection-v1',
              'input': {'path': str(evidence), 'sha256': input_sha, 'rows': len(entries)},
              'output': {'path': str(out), 'sha256': output_digest.hexdigest(), 'rows': written},
              'index': {'path': str(index_path), 'sha256': index_digest.hexdigest(), 'rows': written},
              'parameters': parameters, 'config_sha256': hashlib.sha256(json_bytes(parameters)).hexdigest(),
              'selector': {'commit': commit, 'source_sha256': hashlib.sha256(module.read_bytes()).hexdigest()},
              'per_kind': {'before': {kind: before_kind[kind] for kind in KINDS},
                           'after': {kind: after_kind[kind] for kind in KINDS}},
              'per_supported_type': {'before': {kind: before_support[kind] for kind in supported},
                                     'after': {kind: after_support[kind] for kind in supported}},
              'scenes': {'before': scene_summary(entries), 'after': scene_summary(selected)},
              'label_check_disagreements': {'before': sum(entry.disagreement for entry in entries),
                                             'after': sum(entry.disagreement for entry in selected)},
              'room_size': {'evidence_kind': None, 'supported_type': 'room_size_estimation',
                            'note': 'Room size has no evidence kind.'},
              'selection_attempts': attempts,
              'status': 'selected' if selected else ('empty_input' if not entries else 'infeasible_caps')}
    with selection_path.open('x') as stream:
        stream.write(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + '\n')
    return report


def parser():
    result = argparse.ArgumentParser(description='Select a byte-preserving, scene-balanced trace-evidence subset.')
    result.add_argument('--evidence', type=Path, required=True)
    result.add_argument('--out', type=Path, required=True)
    result.add_argument('--max-rows', type=int, default=MAX_ROWS)
    result.add_argument('--seed', type=int, default=SEED)
    return result


def main(argv=None):
    arguments = parser()
    args = arguments.parse_args(argv)
    try:
        report = select_file(args.evidence, args.out, args.max_rows, args.seed)
    except (ValueError, OSError) as exc:
        arguments.error(str(exc))
    print(json.dumps({key: report[key] for key in ('input', 'output', 'index', 'status')} |
                     {'per_kind': report['per_kind']['after'],
                      'per_supported_type': report['per_supported_type']['after'],
                      'max_scene_share': report['scenes']['after']['max_share']}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
