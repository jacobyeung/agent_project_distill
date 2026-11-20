"""Reviewer check: receipts built on 12 lists refuse under the 13-list config (read-only on the tree)."""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
from student_pilot import r1_launch22 as L
from student_pilot.p3_provenance import file_pin
from student_pilot.row_removals import Removals
from student_pilot.ground_target_filter import TargetFilter

root = Path(tempfile.mkdtemp(prefix='rev24l4c_', dir=Path(__file__).parent))


def jsonl(name, rows):
    path = root / name
    path.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    return file_pin(path)


empty = jsonl('empty.jsonl', [])
other = jsonl('other.jsonl', [dict(row_key='unrelated')])
pointing = jsonl('pointing.jsonl', [dict(row_key='scannet/scene0630_00|3|7')])
twelve = [empty] * 11 + [other]
thirteen = twelve[:-1] + [pointing, other]

# Preparation reader (carrier_c1_run.prepared:689-691) compares receipt pins with Removals(cfg).files.
print('prep pins differ:', twelve != Removals(thirteen).files)
# Pointing receipt and MDG index target-filter settings (carrier_c1_run:545-548, stageb_mdg:169-173).
print('target settings differ:', TargetFilter(twelve, shape_filter=True).settings()
      != TargetFilter(thirteen, shape_filter=True).settings())

# A stale pointing row built without the 13th list is caught by verify_streams/assert_clean.
stale = dict(qid='q1', dataset='scannet', scene='scene0630_00',
             pointing=dict(kind='gt_instance_mask', frame=4, instance_id=7, row_key='scannet/scene0630_00|3|7'))
try:
    Removals(thirteen).assert_clean(stale)
    print('assert_clean: ACCEPTED (bad)')
except ValueError as e:
    print('assert_clean refuses:', str(e)[:60])
# Pointing row without stored row_key: build_stream derives pointing_key = canonical|frame-1|instance.
from student_pilot.ground_target_filter import pointing_key
raw = dict(stale, pointing={k: v for k, v in stale['pointing'].items() if k != 'row_key'})
print('derived pointing_key:', pointing_key(raw), 'removed:', not TargetFilter(thirteen).removals.keep(dict(row_key=pointing_key(raw))))

# Room audit (r1_rooms.verify_audit:95-100): a 12-list audit refuses under a 13-list config.
from student_pilot import r1_rooms
hashes = [p['sha256'] for p in L.REMOVAL_ORDER[:-1] + (L.POINTING_K1_REMOVE, L.NAMING_REMOVE)] if False else \
    list(L.REMOVAL_ORDER[:-1] + (L.POINTING_K1_REMOVE, L.NAMING_REMOVE))
cfg = dict(remove_files=[dict(path='/x/%d' % i, sha256=h) for i, h in enumerate(hashes)],
           r1_training=dict(launch22=dict(removal_order=hashes), row_sources=dict(path='/rs', sha256='a' * 64),
                            room_authority=dict(split=dict(path='/s', sha256='b' * 64))))


def audit_for(pins):
    return dict(schema='r1-room-audit-v1', complete=True, unknown_overlap=0,
                row_sources=cfg['r1_training']['row_sources'], remove_files=pins,
                authority=cfg['r1_training']['room_authority'])


for label, pins in (('12-list audit', [dict(path='/y/%d' % i, sha256=h) for i, h in enumerate(L.REMOVAL_ORDER)]),
                    ('13-list audit', [dict(path='/y/%d' % i, sha256=h) for i, h in enumerate(hashes)])):
    with patch('student_pilot.r1_coverage.deferred', return_value=False), \
            patch('student_pilot.p3_provenance.pinned'), patch.object(r1_rooms, 'pinned'), \
            patch.object(r1_rooms, 'load', return_value=audit_for(pins)):
        try:
            r1_rooms.verify_audit(cfg, dict(path='/a', sha256='c' * 64))
            print(label, 'ACCEPT')
        except ValueError as e:
            print(label, 'refuses:', e)
