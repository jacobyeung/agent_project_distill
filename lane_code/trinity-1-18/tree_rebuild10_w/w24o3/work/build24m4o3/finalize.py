from pathlib import Path
import sys,json,hashlib,shutil,os
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4o3'
sys.path[:0]=[str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
import z
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def kit(n):return L/('out/kit_'+n if n in ('qd','n_go') else 'work/build24/kits/'+n)
base=z.load(D/'BASELINE.json')
assert digest(inventory(L/'work/tree_r1c'))==base['tree']
seals={n:verify(kit(n)) for n in base['kits']};assert seals==base['kits']
rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert {n for n in rcj if rcj[n]!=base['rcj'][n]}=={'x.py','pc.py'}
for name in ('rcj.sh','ps.py','P_SAMPLE_I.json'):assert rcj[name]==base['rcj'][name]
up=z.load(L/'out/UPLOADS_24M4O.json')
files=up['files']
files.append(dict(name='rcj/pc.py',relative_path='out/rcj/pc.py',transfer='local-upload',
    action='replace',baseline_sha256=up['baseline_rcj']['pc.py']))
for row in files:
    p=L/row['relative_path'];row.update(local_path=str(p),sha256=z.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'))
files.sort(key=lambda r:r['name'])
up.update(files=files,total_files=len(files),total_bytes=sum(r['bytes'] for r in files),
          build='24m4o3',unchanged_kit_seals=seals)
assert len(files)==7
write(L/'out/UPLOADS_24M4O3.json',up)
(L/'out/UPLOADS_24M4O3.list').write_text(''.join(r['name']+'\n' for r in files))

# Replay the declared delta from the supplied authenticated baseline bytes.
old=z.load(L/'work/build24m4n/BASELINE.json')
replay=D/'replay';replay.mkdir()
for name,v in old['files']['qd'].items():
    p=kit('qd')/name
    if z.sha(p)!=v['sha256']:p=L/'attic/build24m4n/out/kit_qd'/name
    assert z.sha(p)==v['sha256']
    q=replay/'qd'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());q.chmod(v['mode'])
assert verify(replay/'qd')==up['baseline_kit_seals']['qd']
for name,h in up['baseline_rcj'].items():
    p=L/'out/rcj'/name
    if z.sha(p)!=h:p=L/('attic/build24m4o/out/rcj' if name=='x.py' else 'attic/build24m4o3/out/rcj')/name
    assert z.sha(p)==h
    q=replay/'rcj'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());q.chmod(p.stat().st_mode&511)
for row in files:
    q=replay/row['name'];p=L/row['relative_path']
    if q.exists():
        a=L/'attic/build24m4o3/replay_final'/row['name'];a.parent.mkdir(parents=True,exist_ok=True);q.rename(a)
    q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());q.chmod(int(row['mode'],8))
assert verify(replay/'qd')==seals['qd']
for prefix,source in [('qd',kit('qd')),('rcj',L/'out/rcj')]:
    a={str(p.relative_to(source)):(z.sha(p),p.stat().st_mode&511) for p in source.rglob('*') if p.is_file()}
    b={str(p.relative_to(replay/prefix)):(z.sha(p),p.stat().st_mode&511) for p in (replay/prefix).rglob('*') if p.is_file()}
    assert a==b
write(D/'DELTA_REPLAY.json',dict(status='PASS',files=len(files),exact_bytes_modes=True,baseline=up['baseline_rcj'],rcj=rcj,kits=seals))

checks={n:z.load(D/p) for n,p in [('new','TESTS.json'),('publication','publication/TESTS.json'),
    ('recorder','recorder/RECORDER_TESTS.json'),('contract','contract/RCJ_CONTRACT_TESTS.json'),
    ('sample','sample/SAMPLE_TESTS.json'),('scan','scan/RCJ_SCAN.json')]}
assert all(v['status']=='PASS' for v in checks.values())
write(D/'FAILURES.json',dict(failures=[dict(command='Initial inline edit command',
    output="/bin/bash: -c: line 49: syntax error near unexpected token `('\n/bin/bash: -c: line 49: `            r'[A-Za-z_][\\\\w.]*(?::.*)?', line) and'",
    effect='The shell rejected the command before any edits; the corrected heredoc completed.')],
    failed_tests=[],killed_processes=[],unresolved=[]))
validation=dict(status='PASS',tree_sha256=base['tree'],kits=seals,rcj=rcj,checks=checks,
    mode_b_byte_identical=True,fixture_statuses_preserved=True,tail_bytes_each=65536,
    nd_payload_limit=5000000,total_new_publication_limit=5000000,reason_chars_limit=4096,
    production_executed=False,uploaded=False,launched=False,GO=False,
    qualifications=['Local fixtures only; job 173680 child log remains unavailable.',
        'Tails use the bytes remaining below 5000000 after the three nd outputs; budget_limited marks tails shorter than min(full_size,65536). Existing JSON metadata is outside this new-artifact byte cap.',
        'The reason copies at most 4096 characters of the final exception line found in the last 64 KiB; raw tails are unchanged.'])
write(D/'VALIDATION.json',validation)
lines=[
    'C″ de202f58; kits q de53310b, n 3cf38b0b, n_go 1bb191b9 and qd aaa03e58 verify unchanged.',
    'The outer rcj publisher writes pc_n.log.tail, pc_p.log.tail and rd.log.tail when present, capped at 64 KiB each, with full sizes and SHA256 in timings.json.',
    'N child failures retain FAIL and E95, adding the exit code and final exception line (up to 4,096 characters); raw tail bytes are unchanged.',
    'Eight new tests, twelve publication tests, four recorder tests, rcj contract/sample checks, name scanning and exact delta replay pass; tested statuses and mode b bytes match.',
    'nd.py remains byte-identical; tails share the remaining sub-5 MB artifact budget, with budget_limited=true if space forces a shorter tail; JSON metadata is separate.',
    'UPLOADS_24M4O3.json/.list declare seven files against Orchard qd 7d358ff5 and the stated rcj pins; superseded bytes remain in attic.',
    'No production job or upload ran; the actual E95 cause remains unknown. VALIDATION.json records limits; FAILURES.json records the rejected shell command.'
]
assert len(lines)<8
(L/'out/BUILD24M4O3_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='PASS',upload_files=len(files),upload_bytes=up['total_bytes'],kits=seals),indent=2))
