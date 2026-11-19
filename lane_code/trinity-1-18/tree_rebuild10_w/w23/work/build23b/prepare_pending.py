from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/'work/build23b'
p=D/'finish.py';s=p.read_text();a=s.index("capacity=J.load(D/'CAPACITY.json')");b=s.index('# Count changed executable statements',a)
s=s[:a]+'''import datetime
from student_pilot.p3_provenance import file_pin
root=D/'proofs/400/q/p'
stage='native_frame_audit' if not (root/'phase_frames.complete.json').exists() else 'population_or_loader_audit'
fixture=[]
pending=dict(status='INCOMPLETE',GO=False,source_seal=kit['tree_seal'],stage=stage,
    checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    preparation_marker=file_pin(root/'phase_prepare.complete.json'),
    preparation=J.load(Path(J.load(root/'phase_prepare.complete.json')['payload']['path'])),
    note='Native preparation completed. The capacity replay remains running at the packaging deadline cutoff; no new ADMIT or rank loss is claimed. The running proof writes CAPACITY.json when complete.')
J.write(D/'CAPACITY_PENDING.json',pending);J.write(D/'FIXTURE.json',pending)
''' +s[b:]
s=s.replace('PASS: review 23 MUST fixed; MINIMAL CPU proof ADMIT. Production GO=false.', 'GO AFTER FIX: review 23 MUST fixed; capacity replay incomplete at packaging cutoff. Production GO=false.')
s=s.replace('Every recorded loss is finite; every deferred count/draw is zero. Final-tree source pins, rows and all per-stream losses: work/build23b/FIXTURE.json.', 'Capacity: native 400 preparation completed; the full frame audit remains running. No new ADMIT or finite-rank-loss claim; 600 was not rerun.')
s=s.replace('400 reruns native preparation, population, production audit, handover and forward; 600 reuses those stores and reruns checkpoint handover/forward.', 'Snapshot and authenticated preparation metadata: work/build23b/CAPACITY_PENDING.json. The running replay writes work/build23b/CAPACITY.json on completion.')
s=s.replace("print(json.dumps(dict(status='PASS',tests=total", "print(json.dumps(dict(status='CAPACITY_PENDING',tests=total")
(D/'finish_pending.py').write_text(s)
p=D/'package.py';s=p.read_text().replace("for name in ('FIXTURE.json','SCAN.json','INTEGRITY.json'):assert read(D/name)['status']=='PASS'", "for name in ('SCAN.json','INTEGRITY.json'):assert read(D/name)['status']=='PASS'\npending=read(D/'FIXTURE.json')['status']=='INCOMPLETE'\nassert pending or read(D/'FIXTURE.json')['status']=='PASS'")
s=s.replace("for p in D.rglob('*'):\n", "for p in D.rglob('*'):\n if pending and (p.is_relative_to(D/'proofs') or p.name in ('capacity_final.log','CAPACITY.json')):continue\n")
s=s.replace("'DELIVERY.json is external to avoid a circular package checksum.'])", "'DELIVERY.json is external to avoid a circular package checksum.',\n 'The active capacity output is omitted when pending; CAPACITY_PENDING.json records the authenticated preparation snapshot.'])")
p.write_text(s)
