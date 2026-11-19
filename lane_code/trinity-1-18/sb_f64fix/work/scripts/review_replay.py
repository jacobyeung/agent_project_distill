"""Replay review sb_f64rev's counterexamples against the fixed kit; writes out/review_replay.json."""
import copy
import hashlib
import importlib.machinery
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT.parent / 'sb_f64'
REV = ROOT.parent / 'sb_f64rev' / 'out'
KIT = ROOT / 'kit'
sys.path[:0] = [str(KIT / 'scripts'), str(KIT / 'read')]
tmp = ROOT / 'work' / 'replay'
tmp.mkdir(parents=True, exist_ok=False)


def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes)) and (args[2] or 0) & (
            os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
        if not Path(os.fsdecode(args[0])).absolute().is_relative_to(ROOT):
            raise RuntimeError('write outside workspace: ' + os.fsdecode(args[0]))


sys.addaudithook(guard)
from student_pilot import frame_input as F  # noqa: E402
from student_pilot.carrier_c1_data import layout_inputs  # noqa: E402
import f64_read as R  # noqa: E402
import nest_store  # noqa: E402
import token_audit  # noqa: E402


def refused(call):
    try:
        return dict(refused=False, value=call())
    except ValueError as error:
        return dict(refused=True, reason=str(error))


def first_row(path):
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        return json.loads(db.execute('SELECT row FROM rows ORDER BY i LIMIT 1').fetchone()[0])


seen = {}
out = {}
out['export_without_frame_input'] = refused(
    lambda: R.training_layout({'frame_layout': 'duplicate'}, {'frame_count': 32, 'frame_input': F.NESTED}))
reader_root = ROOT / 'work' / 'reader_root'
out['install_src_b_f64_read'] = dict(
    found_at_src_b=importlib.machinery.PathFinder.find_spec('f64_read', [str(reader_root)]) is not None,
    documented_as=json.loads((KIT / 'read' / 'READ_CONFIG_F64.json').read_text())['code']['module']['install_as'])
for name, files in (('empty_shard', [REV / 'empty_coverage.jsonl']),
                    ('single_pose_row', [REV / 'partial_coverage.jsonl']),
                    ('single_pose_row_twice', [REV / 'partial_coverage.jsonl'] * 2)):
    summary = token_audit.summarize([str(f) for f in files])
    out[name] = dict(launch_ready=summary['launch_ready'], errors=summary['errors'])
    seen.update({str(f): token_audit.file_sha256(f) for f in files})
store = SRC / 'work/dryrun/n32/a43/pose/rows.sqlite'
target = tmp / 'empty_nested.sqlite'
report = nest_store.apply(store, {}, target)
out['nest_store_missing_pins'] = dict(status=report['status'], published=report['published'],
                                      output_exists=target.exists(), counts=report['counts'],
                                      first_reason=report['refused'][0]['reason'])
seen[str(store)] = token_audit.file_sha256(store)
source = copy.deepcopy(first_row(store))
filled = first_row(SRC / 'work/dryrun/f64/a43/pose/rows.sqlite')
for key in ('frames', 'frame_indices', 'timestamps'):
    source['student_input'][key].reverse()
layout_inputs(source, 'duplicate', frame_count=32)
pins = dict(zip(filled['student_input']['frame_indices'], filled['student_input']['frames'], strict=True))
out['reversed_anchors'] = refused(lambda: nest_store.nest(source, pins, verify=lambda pin: None))
out['reviewer_artifacts_sha256'] = seen
expected = dict(export_without_frame_input=out['export_without_frame_input']['refused'],
                install=out['install_src_b_f64_read']['found_at_src_b'],
                empty=not out['empty_shard']['launch_ready'], single=not out['single_pose_row']['launch_ready'],
                twice=not out['single_pose_row_twice']['launch_ready'],
                missing_pins=not out['nest_store_missing_pins']['published'] and not target.exists(),
                reversed=out['reversed_anchors']['refused'])
out['all_counterexamples_refused'] = all(expected.values())
(ROOT / 'out' / 'review_replay.json').write_text(json.dumps(out, indent=2, default=str) + '\n')
print(json.dumps(dict(expected, all=out['all_counterexamples_refused']), indent=2))
sys.exit(0 if out['all_counterexamples_refused'] else 1)
