"""64-viewpoint student frames for the RGB-only reader, built with the trainer's own nesting code.

The reader's student row is `parity.trainer_row` (32 anchors from FRAMES.json) passed through
`student_pilot.frame_input.nest_row`, the function that nests training rows, with pins from a
student manifest. The G3T tower keeps its own dense manifest; only the student's frames change.
Install as `src/b/f64_read.py`, a top-level module beside the `src/b/e2e_reader` package: the patched
`parity.py` imports it absolutely (`from f64_read import ...`) with `src/b` on sys.path.
Needs the trainer tree (tree_f64) on sys.path.
"""
import hashlib
import json
from pathlib import Path

READ_FRAMES = {'layout': 'duplicate', 'count': 64, 'anchors': 32, 'rule': 'nested_bisection_v1'}
LAYOUT_KEYS = ('layout', 'count', 'anchors', 'rule')
MANIFEST_SCHEMA = 'f64-student-frames-v1'


def training_layout(artifact, config):
    """Frame layout an export trained with. A nested export declares the same valid frame_input in
    artifact.json and in its training config; a 32-viewpoint export declares it in neither."""
    from student_pilot.frame_input import check_spec
    spec = artifact.get('frame_input')
    if spec is not None or config.get('frame_input') is not None:
        if 'frame_input' not in artifact:
            raise ValueError('export_frame_input_absent')
        if spec != config.get('frame_input'):
            raise ValueError('export_frame_input_differs_from_config')
        check_spec(spec)
    layout = dict(layout=artifact['frame_layout'], count=spec['viewpoints'] if spec else int(config.get('frame_count', 32)))
    if spec:
        layout.update(anchors=spec['anchors'], rule=spec['rule'])
    return layout


def check_layout(read_frames, export_layout):
    """Every layout key must agree; a 32-frame export has no anchors/rule and refuses a nested read."""
    differs = {k: (read_frames.get(k), export_layout.get(k)) for k in LAYOUT_KEYS
               if read_frames.get(k) != export_layout.get(k)}
    if differs:
        raise ValueError('read_frame_layout_differs_from_training: %r' % differs)
    return dict(read_frames, matches_training=True)


def _captures(frames_json):
    data = json.loads(Path(frames_json).read_text()) if isinstance(frames_json, (str, Path)) else frames_json
    captures = data['captures']
    return {c['native']: c for c in captures} if isinstance(captures, list) else captures


def plan_manifest(frames_json):
    """Ordinals the student reads for each capture and the ones a frame host must decode (no pixels here)."""
    from student_pilot.carrier_c1_data import nested_indices
    out = {}
    for native, c in sorted(_captures(frames_json).items()):
        anchors = c['anchor_indices']
        indices, slots = nested_indices(anchors, READ_FRAMES['count'])
        if indices[-1] >= c['total_num_frames']:
            raise ValueError('nested ordinal beyond the clip: ' + native)
        out[native] = dict(frame_indices=indices, anchor_slots=slots, fps=c['fps'],
                           total_num_frames=c['total_num_frames'],
                           decode=[k for k in indices if k not in set(anchors)])
    return dict(schema=MANIFEST_SCHEMA, rule=READ_FRAMES['rule'], captures=out)


def check_manifest_entry(capture, entry):
    """A filled entry: the planned ordinals, the anchors' own pins, and one pin per bisection frame."""
    from student_pilot.carrier_c1_data import nested_indices
    indices, slots = nested_indices(capture['anchor_indices'], READ_FRAMES['count'])
    if (entry.get('frame_indices'), entry.get('anchor_slots')) != (indices, slots):
        raise ValueError('student manifest differs from the nesting rule')
    pins = entry.get('pins') or {}
    missing = [k for k in entry['decode'] if not isinstance(pins.get(str(k)), dict)]
    if missing:
        raise ValueError('student manifest lacks decoded frames: %r' % missing[:4])
    return {int(k): dict(path=v['path'], sha256=v['sha256']) for k, v in pins.items()}


def student_row(row32, capture, entry, verify=None):
    """parity.trainer_row output -> the nested row training feeds the student, with a 64-frame identity."""
    from student_pilot.frame_input import NESTED, check_row, nest_row
    anchors = row32['student_input']['frame_indices']
    if anchors != capture['anchor_indices'] or any(a >= b for a, b in zip(anchors, anchors[1:])):
        raise ValueError('student anchors must follow the capture in strictly increasing order')
    pins = check_manifest_entry(capture, entry)
    if verify is not None:
        for pin in pins.values():
            verify(pin['path'], pin['sha256'])
    row = nest_row(row32, pins)
    check_row(row, NESTED)
    si = row['student_input']
    identity = {k: si[k] for k in ('frame_indices', 'fps', 'total_num_frames')}
    identity['frames'] = [f['sha256'] for f in si['frames']]
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'),
                                       allow_nan=False).encode()).hexdigest()
    si['video_identity'] = dict(video_sha256=digest, kind='devS1-pinned-PNG-clip-nested64-v1')
    return row


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Plan the student manifest from FRAMES.json')
    parser.add_argument('frames_json')
    parser.add_argument('out')
    args = parser.parse_args()
    value = plan_manifest(args.frames_json)
    Path(args.out).write_text(json.dumps(value, indent=1, sort_keys=True) + '\n')
    print(len(value['captures']), 'captures,', sum(len(c['decode']) for c in value['captures'].values()), 'frames to decode')


if __name__ == '__main__':
    main()
