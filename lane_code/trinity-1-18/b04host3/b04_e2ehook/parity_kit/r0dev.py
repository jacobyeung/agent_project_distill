"""Build the held-out R0-dev f32 read inputs without changing the reader."""
import argparse
import ast
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

from parity_kit.common import LANE, TASKS, key, read, rows, sha

RESERVE = Path('/scratch/jjyeung/orch_n30/b10_reserve')
QUESTIONS = RESERVE / 'out/qsets/R0_QUESTIONS_dev_f32.jsonl'
SUMMARY = RESERVE / 'out/qsets/R0_QUESTIONS_SUMMARY.json'
MANIFEST = RESERVE / 'out/FRAMES_MANIFEST.json'
SCENE_MANIFESTS = RESERVE / 'out/frame_manifests'
FRAMES_ROOT = RESERVE / 'frames'
BASE_SETTINGS = LANE / 'parity_kit/settings_118b.json'
DEFAULT_OUT = LANE / 'parity_kit/r0dev'
EXPECTED_COUNTS = {
    'object_counting': 385, 'object_size_estimation': 293,
    'object_abs_distance': 290, 'object_rel_distance': 279,
    'obj_appearance_order': 246, 'object_rel_direction_easy': 192,
    'object_rel_direction_medium': 194, 'object_rel_direction_hard': 192,
    'room_size_estimation': 98,
}
INPUT_PREFIXES = {
    QUESTIONS: 'b4e278f2', SUMMARY: '8444684f', MANIFEST: '450e4125',
}
# The unchanged runner checks this contract against reader_policy.DECODE_BUDGET.
DECODE_BUDGET = dict(thinking_tokens=2048, answer_tokens=64,
                     max_new_tokens=16384, max_calls=200,
                     call_window_tokens=96, counting='sampled_callbacks')
OUTPUT_NAMES = ('TASKS_R0DEV.jsonl', 'FRAMES_R0DEV.json', 'DENSE_R0DEV.json',
                'request_r0dev.json', 'settings_r0dev.json', 'BUILD_R0DEV.json')


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def write_new(path, data):
    """Never replace an existing file, including a previous build or report."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def _load_scene(scene, entry):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', scene):
        raise ValueError('invalid scene: ' + scene)
    path = SCENE_MANIFESTS / (scene + '.json')
    digest = sha(path)
    if digest != entry['manifest_sha256']:
        raise ValueError('scene manifest sha256 mismatch: ' + scene)
    manifest = read(path)
    if manifest['scene'] != scene or entry.get('deferred') or entry['r0_split'] != 'R0-dev':
        raise ValueError('scene is not an available R0-dev scene: ' + scene)
    return manifest, dict(path=str(path), sha256=digest)


def _validate_row(row, manifest):
    if row['r0_split'] != 'R0-dev' or row['dataset'] != 'scannetpp':
        raise ValueError('expected held-out R0-dev scannetpp row')
    indices = row['frame_indices']
    if (indices != manifest['layout_f32'] or len(indices) != 32
            or row['num_frames'] != 32
            or any(type(i) is not int for i in indices)):
        raise ValueError('row frame_indices differ from layout_f32: ' + row['qid'])
    fps, total = row['fps'], row['total_num_frames']
    if (not math.isfinite(fps) or fps <= 0 or type(total) is not int
            or total != manifest['total_decoded']
            or any(not 0 <= i < total for i in indices)):
        raise ValueError('invalid frame timing: ' + row['qid'])


def _capture(row, manifest):
    frames = []
    for index in manifest['layout_f32']:
        digest = manifest['frames'].get(str(index))
        path = f"scannetpp/{row['scene']}/{index:06d}.png"
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('missing frame sha256: ' + path)
        if not (FRAMES_ROOT / path).is_file():
            raise ValueError('missing frame: ' + path)
        frames.append(dict(index=index, path=path, sha256=digest))
    return dict(native='r0dev/' + row['scene'], scene=row['scene'],
                anchor_indices=row['frame_indices'], frames=frames,
                timestamps=[i / row['fps'] for i in row['frame_indices']],
                fps=row['fps'], total_num_frames=row['total_num_frames'],
                hw=list(reversed(manifest['size'])))


def build(out_dir=DEFAULT_OUT):
    """Validate metadata and frame presence, then create six deterministic files.

    PNG contents are checked by bind_item(verify=True); the build only stats PNGs.
    Appearance order uses the same existing exact-match scorer as VSI choices.
    """
    out = Path(out_dir).resolve()
    for name in OUTPUT_NAMES:
        if (out / name).exists():
            raise FileExistsError(out / name)
    inputs = {}
    for path in (*INPUT_PREFIXES, TASKS[0], BASE_SETTINGS):
        digest = sha(path)
        if path in INPUT_PREFIXES and not digest.startswith(INPUT_PREFIXES[path]):
            raise ValueError('input sha256 prefix mismatch: ' + str(path))
        inputs[path.name] = dict(path=str(path), sha256=digest)
    source = rows(QUESTIONS)
    counts = Counter(r['question_type'] for r in source)
    if counts != EXPECTED_COUNTS:
        raise ValueError('unexpected R0-dev type counts: ' + str(counts))
    qid_counts = Counter(r['qid'] for r in source)
    duplicates = {qid: n for qid, n in qid_counts.items() if n > 1}
    seen = Counter()  # a repeated qid keeps its first row as qid and numbers later rows qid#2, qid#3, ...
    scorers = {}
    for task in rows(TASKS[0]):
        kind, scorer = task['question_type'], task['scorer']
        if kind in scorers and scorers[kind] != scorer:
            raise ValueError('inconsistent dev-S1 scorer: ' + kind)
        scorers[kind] = scorer
    scorers.setdefault('obj_appearance_order', scorers['object_rel_distance'])
    index = read(MANIFEST)['scenes']
    captures, dense, scenes, scene_pins, tasks = {}, {}, {}, {}, []
    for row in source:
        scene = row['scene']
        native = 'r0dev/' + scene
        if scene not in scenes:
            scenes[scene], scene_pins[scene] = _load_scene(scene, index['scannetpp/' + scene])
        manifest = scenes[scene]
        _validate_row(row, manifest)
        if native not in captures:
            captures[native] = _capture(row, manifest)
            dense[native] = dict(native=native, frames=captures[native]['frames'],
                                 anchor_slots=list(range(32)))
        capture = captures[native]
        if (capture['fps'], capture['total_num_frames']) != (row['fps'], row['total_num_frames']):
            raise ValueError('inconsistent scene timing: ' + scene)
        options = row['options']
        if isinstance(options, str):
            options = ast.literal_eval(options)
        if not isinstance(options, list) or not all(isinstance(s, str) for s in options):
            raise ValueError('options must be a list of strings: ' + row['qid'])
        seen[row['qid']] += 1
        tid = row['qid'] if seen[row['qid']] == 1 else '%s#%d' % (row['qid'], seen[row['qid']])
        tasks.append(dict(id=tid, source_qid=row['qid'], native=native, room=native, scene=scene,
                          dataset=row['dataset'], question_type=row['question_type'],
                          question=row['question'], options=options, answer=row['answer'],
                          ground_truth=row['answer'], released_answer=None,
                          source_frame_indices=row['frame_indices'], fps=row['fps'],
                          total_num_frames=row['total_num_frames'],
                          answer_type='multiple_choice' if options else 'numeric',
                          scorer=scorers[row['question_type']]))
    request = dict(keys=[key(t) for t in tasks], decode_budget=DECODE_BUDGET,
                   prompt_flag=None, arm='unflagged', layout='duplicate')
    settings = dict(read(BASE_SETTINGS), tasks=[str(out / OUTPUT_NAMES[0])],
                    frames_json=str(out / OUTPUT_NAMES[1]),
                    dense_manifest=str(out / OUTPUT_NAMES[2]),
                    request=str(out / OUTPUT_NAMES[3]), frames_root=str(FRAMES_ROOT))
    payloads = {
        OUTPUT_NAMES[0]: ''.join(json.dumps(t, sort_keys=True, allow_nan=False) + '\n'
                                 for t in tasks).encode(),
        OUTPUT_NAMES[1]: json_bytes(dict(captures=captures)),
        OUTPUT_NAMES[2]: json_bytes(dict(captures=dense)),
        OUTPUT_NAMES[3]: json_bytes(request),
        OUTPUT_NAMES[4]: json_bytes(settings),
    }
    if len({t['id'] for t in tasks}) != len(tasks):
        raise ValueError('R0-dev task ids are not unique')
    receipt = dict(schema='r0dev-f32-v1', inputs=inputs, scene_manifests=scene_pins,
                   duplicate_source_qids=dict(sorted(duplicates.items())),
                   counts=dict(tasks=len(tasks), scenes=len(scenes),
                               frames=sum(len(c['frames']) for c in captures.values()),
                               per_type=dict(sorted(counts.items()))),
                   scorers={t: scorers[t] for t in sorted(counts)},
                   scorer_notes={'obj_appearance_order':
                                 'Uses the existing VSI exact-match scorer; absent from dev-S1 examples.'},
                   output_sha256s={n: hashlib.sha256(b).hexdigest() for n, b in payloads.items()})
    payloads[OUTPUT_NAMES[5]] = json_bytes(receipt)
    for name, data in payloads.items():
        write_new(out / name, data)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(build(args.out)['counts'], sort_keys=True))


if __name__ == '__main__':
    main()
