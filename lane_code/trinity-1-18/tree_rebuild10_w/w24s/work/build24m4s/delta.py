from pathlib import Path
import json, sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4s'
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
from common import kit, write, NAMES
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

base=json.loads((D/'BASELINE.json').read_bytes())
assert digest(inventory(L/'work/tree_r1c'))==base['tree']
seals={n:verify(kit(n)) for n in NAMES}
def files(k):
    return {str(p.relative_to(k)):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
new={n:files(kit(n)) for n in NAMES}
assert {p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}==base['rcj']
rows=[];optional=[]
for n in NAMES:
    assert set(new[n])==set(base['files'][n])
    for name,v in sorted(new[n].items()):
        old=base['files'][n][name]
        if v==old:continue
        assert name in ('b/sc.py','BUILD.json','SHA256SUMS.txt')
        path=kit(n)/name
        entry=dict(name=n+'/'+name,relative_path=str(path.relative_to(L)),local_path=str(path),action='replace',baseline_sha256=old['sha256'],sha256=v['sha256'],bytes=v['bytes'],mode=format(v['mode'],'04o'),transfer='local-upload')
        (optional if n=='n_go' else rows).append(entry)
rows.sort(key=lambda v:v['name']);optional.sort(key=lambda v:v['name'])
assert len(rows)==9 and len(optional)==3
up=dict(schema='cpu-publication-delta-v1',build='24m4s',baseline='Exact supplied Orchard pins',baseline_kit_seals={n:base['kits'][n] for n in ('q','n','qd')},baseline_rcj=base['rcj'],tree_sha256=base['tree'],kit_seals={n:seals[n] for n in ('q','n','qd')},files=rows,total_files=len(rows),total_bytes=sum(v['bytes'] for v in rows),GO=False,uploaded=False,launched=False,config_delta=False)
write(L/'out/UPLOADS_24M4S.json',up)
(L/'out/UPLOADS_24M4S.list').write_text(''.join(v['name']+'\n' for v in rows))
write(L/'out/UPLOADS_24M4S_GO.json',dict(schema='optional-kit-overlay-v1',build='24m4s',baseline_kit_seal=base['kits']['n_go'],kit_seal=seals['n_go'],files=optional,total_files=3,total_bytes=sum(v['bytes'] for v in optional),applied=False,uploaded=False,launched=False))
(L/'out/UPLOADS_24M4S_GO.list').write_text(''.join(v['name']+'\n' for v in optional))

replay=D/'replay';replay.mkdir()
def copy(p,q,mode):
    q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as stream:stream.write(p.read_bytes())
    q.chmod(mode)
for n in NAMES:
    for name,v in base['files'][n].items():
        p=kit(n)/name
        if z.sha(p)!=v['sha256']:p=L/'attic/build24m4s'/p.relative_to(L)
        assert z.sha(p)==v['sha256']
        copy(p,replay/n/name,v['mode'])
    assert verify(replay/n)==base['kits'][n]
for name,h in base['rcj'].items():
    p=L/'out/rcj'/name;assert z.sha(p)==h
    copy(p,replay/'rcj'/name,p.stat().st_mode&511)
for row in rows+optional:
    q=replay/row['name'];a=L/'attic/build24m4s/replay'/row['name'];a.parent.mkdir(parents=True,exist_ok=True);q.rename(a)
    copy(L/row['relative_path'],q,int(row['mode'],8))
for n in NAMES:
    assert verify(replay/n)==seals[n]
    assert files(replay/n)==new[n]
assert files(replay/'rcj')==files(L/'out/rcj')
write(D/'DELTA_REPLAY.json',dict(status='PASS',ordinary_files=len(rows),optional_files=len(optional),rcj_changed_files=0,exact_bytes_modes=True,baseline_kit_seals=base['kits'],baseline_rcj=base['rcj'],kits=seals))
print(json.dumps(dict(status='PASS',ordinary_files=len(rows),optional_files=len(optional),kits=seals),indent=2))
