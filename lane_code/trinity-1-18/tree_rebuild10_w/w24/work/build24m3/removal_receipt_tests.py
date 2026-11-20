from common import *
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import file_pin
from student_pilot.r1_rooms import census,verify_audit
from student_pilot.ground_target_filter import TargetFilter
sys.path.insert(0,str(kit('q')/'b'))
import i
F=D/'removal_receipts';F.mkdir()
cfg=J.load(L/'work/build24/proofs/capacity/400/request_config.json')
paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m1/UPLOADS_q.json')['files'] if x['opaque_name'].startswith('u/')}
paths.update(cfg['r1_training']['persisted_files'])
point=D/'u/d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1'
paths[J.sha(point)]=str(point)
old_settings=TargetFilter(cfg['remove_files'],shape_filter=True).settings()
cfg['remove_files'].insert(-1,dict(file_pin(point),role='protected_rooms',stream='pointing'))
cfg['r1_training']['launch22']['removal_order']=[p['sha256'] for p in cfg['remove_files']]
pin=J.write(F/'cfg.json',cfg)
with scope(paths):
 request=i.refresh(dict(config=pin,staged_pins=[pin]),F/'pool')
 after=J.load(request['config']['path'])
 refreshed=J.load(after['s1_routing']['selection']['path'])
 assert i.normalized(refreshed['remove_files'])==i.normalized(cfg['remove_files'])
 assert J.load(F/'pool/r.json')['removals_regenerated'] is True
 assert TargetFilter(cfg['remove_files'],shape_filter=True).settings()!=old_settings
 audit,_=census(after)
 audit_pin=J.write(F/'rooms.json',audit)
 verify_audit(after,audit_pin)
J.write(D/'REMOVAL_RECEIPT_TESTS.json',dict(status='PASS',native_pool_refresh=True,native_room_audit_regenerated_and_verified=True,target_settings_change=True,fixture='Retained native24 synthetic sources; actual 320-key pointing list; native functions unchanged.'))
print('Native changed-removal pool, room audit and target settings PASS')
