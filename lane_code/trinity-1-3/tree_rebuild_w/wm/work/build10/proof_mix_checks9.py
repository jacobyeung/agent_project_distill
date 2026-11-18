"""Exercise real kit read-checks on bounded synthetic metadata, including tampering."""
import base64,hashlib,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1';O=L/'work/merge11/proofs/mix_checks'
O.mkdir(exist_ok=True);sys.path[:0]=[str(T),str(B)]
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.p3_provenance import sha256
from launch_r2.build import capsule_json,verify as verify2
from launch_r1.build import verify as verify1
def put(root,name,value):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(capsule_json(value));return dict(path=name,sha256=sha256(p))
def seal(root,r2):
    (root/'b').mkdir(exist_ok=True)
    (root/'b/wh.json').write_bytes((T/'launch_s1/b/wh.json').read_bytes())
    (root/'job.sh').write_text('#!/bin/bash\ntrue\n')
    names={str(p.relative_to(root)):sha256(p) for d in ('b','k') for p in (root/d).rglob('*') if p.is_file()}
    names['job.sh']=sha256(root/'job.sh')
    (root/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(names.items())))
    if r2:(root/'ANON_OK.json').write_text(json.dumps(dict(status='CLEAN',hits=0,manifest_sha256=sha256(root/'SHA256SUMS.txt'))))
def refusal(fn,message):
    try:fn()
    except ValueError as error:assert message in str(error),str(error)
    else:raise AssertionError('Tampered mix admitted')
records=[]
root=O/'r1';root.mkdir(exist_ok=True)
raw=b'{}\n';pin=dict(path='u/a.json',sha256=hashlib.sha256(raw).hexdigest())
put(root,'k/c.json',dict(r1_training=dict(mix=pin)))
put(root,'k/s.json',dict(entries={pin['path']:dict(payload=base64.b64encode(raw).decode())}))
put(root,'k/8.json',dict(report_sha256=pin['sha256']));seal(root,False);verify1(root)
put(root,'k/8.json',dict(report_sha256='0'*64));seal(root,False)
refusal(lambda:verify1(root),'R1_KIT_MIX_EVIDENCE_DIFFERS');records.append('r1_report_mismatch_refused')
root=O/'r2';root.mkdir(exist_ok=True)
base=put(root,'k/1.json',{});deployment=dict(file=base['path'],sha256=base['sha256'])
put(root,'k/0.json',dict(trainer=deployment,record=deployment))
mix=put(root,'k/2.json',dict(cells=[]))
cfg=put(root,'k/c.json',dict(r2_build2=dict(mix=mix)))
put(root,'k/launch.json',dict(config=dict(file=cfg['path'],sha256=cfg['sha256'])))
put(root,'k/8.json',dict(mix=mix,report_sha256=mix['sha256']));seal(root,True);verify2(root)
put(root,'k/8.json',dict(mix=mix,report_sha256='0'*64));seal(root,True)
refusal(lambda:verify2(root),'KIT_MIX_EVIDENCE_DIFFERS');records.append('r2_report_mismatch_refused')
put(root,'k/8.json',dict(mix=mix,report_sha256=mix['sha256']))
cfg=put(root,'k/c.json',dict(r2_build2=dict(mix=base)))
put(root,'k/launch.json',dict(config=dict(file=cfg['path'],sha256=cfg['sha256'])));seal(root,True)
refusal(lambda:verify2(root),'KIT_MIX_CONFIG_DIFFERS');records.append('r2_config_mismatch_refused')
monitor.save(O)
(O/'RESULT.json').write_text(json.dumps(dict(passed=records,scope='Synthetic metadata only; real kit verify functions; complete delivered kits checked separately.'),indent=2)+'\n')
print(json.dumps(records))
