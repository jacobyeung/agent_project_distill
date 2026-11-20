from common import *
from unittest.mock import patch
from contextlib import ExitStack
from student_pilot.r1_persisted import scope
from student_pilot import r1_rooms as R,r1_direction_twins as W
from student_pilot.ground_target_filter import TargetFilter
sys.path.insert(0,str(kit('q')/'b'));import i
F=D/'removal_receipts';cfg=J.load(F/'cfg.json');after=J.load(F/'pool/c.json')
paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m1/UPLOADS_q.json')['files'] if x['opaque_name'].startswith('u/')}
paths.update(cfg['r1_training']['persisted_files'])
point=D/'u/d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1';paths[J.sha(point)]=str(point)
twins=cfg['r1_training']['direction_twins']
with scope(paths),ExitStack() as context:
 for key in ('rows','binding','aliases'):context.enter_context(patch.object(W,key.upper(),twins[key]['sha256']))
 context.enter_context(patch.object(R,'STORE',J.load(cfg['streams']['vqa']['path'])['database']['sha256']))
 audit,_=R.census(after);audit_pin=J.write(F/'rooms.json',audit);R.verify_audit(after,audit_pin)
 refreshed=J.load(after['s1_routing']['selection']['path'])
 assert i.normalized(refreshed['remove_files'])==i.normalized(cfg['remove_files'])
 assert J.load(F/'pool/r.json')['removals_regenerated'] is True
 old=J.load(L/'work/build24/proofs/capacity/400/request_config.json')
 assert TargetFilter(cfg['remove_files'],shape_filter=True).settings()!=TargetFilter(old['remove_files'],shape_filter=True).settings()
J.write(D/'REMOVAL_RECEIPT_TESTS.json',dict(status='PASS',native_pool_refresh=True,native_room_audit_regenerated_and_verified=True,target_settings_change=True,fixture='Retained native24 synthetic sources and twin authority constants; actual 320-key list; native functions unchanged.'))
print('Native changed-removal pool, room audit and target settings PASS')
