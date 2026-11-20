from pathlib import Path
import json, sys, hashlib, os
L=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
sys.path[:0]=[str(L/'out/kit_qd/b'),str(L/'work/tree_r1c')]
import z
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
def write(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def kit(n):return L/('out/kit_'+n if n in ('qd','n_go') else 'work/build24/kits/'+n)
def files(path):return {str(p.relative_to(path)):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in path.rglob('*') if p.is_file()}
base=z.load(L/'work/build24m4s/BASELINE.json');candidate=z.load(D/'BASELINE.json')
assert digest(inventory(L/'work/tree_r1c'))==base['tree']==candidate['tree']
assert {n:h[:8] for n,h in base['kits'].items() if n!='n_go'}==dict(q='e7ac0727',n='a7809da0',qd='221d1782')
assert base['rcj']['x.py'].startswith('d8517333') and candidate['rcj']['x.py'].startswith('283a46ca')
assert candidate['kits']['qd'].startswith('291c6f58')
seals={n:verify(kit(n)) for n in ('q','n','qd','n_go')}
assert seals==candidate['kits']
now={n:files(kit(n)) for n in seals};rcj=files(L/'out/rcj')
assert {n for n,v in rcj.items() if v['sha256']!=candidate['rcj'][n]}=={'x.py','nd.py'}
def row(name,p,old):
    return dict(name=name,relative_path=str(p.relative_to(L)),local_path=str(p),action='replace',
        baseline_sha256=old,sha256=z.sha(p),bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),transfer='local-upload')
rows=[];optional=[]
for n in seals:
    assert set(now[n])==set(base['files'][n])
    for rel,v in sorted(now[n].items()):
        if v['sha256']!=base['files'][n][rel]['sha256']:
            (optional if n=='n_go' else rows).append(row(n+'/'+rel,kit(n)/rel,base['files'][n][rel]['sha256']))
for n,v in rcj.items():
    if v['sha256']!=base['rcj'][n]:rows.append(row('rcj/'+n,L/'out/rcj'/n,base['rcj'][n]))
rows.sort(key=lambda v:v['name']);optional.sort(key=lambda v:v['name'])
cr=[row('rcj/'+n,L/'out/rcj'/n,candidate['rcj'][n]) for n in sorted(rcj) if rcj[n]['sha256']!=candidate['rcj'][n]]
assert len(rows)==14 and len(optional)==4 and len(cr)==2
for suffix,entries,oldkits,newkits,oldrcj in [('',rows,{n:base['kits'][n] for n in ('q','n','qd')},{n:seals[n] for n in ('q','n','qd')},base['rcj']),
        ('_CANDIDATE',cr,{'qd':candidate['kits']['qd']},{'qd':seals['qd']},candidate['rcj']),
        ('_GO',optional,{'n_go':base['kits']['n_go']},{'n_go':seals['n_go']},base['rcj'])]:
    value=dict(schema='cpu-publication-delta-v1',build='24m4u',baseline_kit_seals=oldkits,kit_seals=newkits,
        baseline_rcj=oldrcj,tree_sha256=base['tree'],files=entries,total_files=len(entries),total_bytes=sum(r['bytes'] for r in entries),
        GO=False,uploaded=False,launched=False,config_delta=False,extent_candidate_status='BLOCKED: no supported scope and incomplete carry')
    write(L/'out'/('UPLOADS_24M4U'+suffix+'.json'),value)
    (L/'out'/('UPLOADS_24M4U'+suffix+'.list')).write_text(''.join(r['name']+'\n' for r in entries))
def original(p,h):
    for source in [p,*[L/'attic'/b/p.relative_to(L) for b in ('build24m4u','build24m4t','build24m4s')]]:
        if source.is_file() and z.sha(source)==h:return source
    raise ValueError('Missing baseline: '+str(p))
def copy(p,q):
    q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as stream:stream.write(p.read_bytes())
    q.chmod(p.stat().st_mode&511)
records=[]
for label,old,changes,names in [('reviewed',base,rows+optional,tuple(seals)),('candidate',candidate,cr,('qd',))]:
    dest=D/(label+'_replay');dest.mkdir()
    for n in names:
        for rel,v in old['files'][n].items():copy(original(kit(n)/rel,v['sha256']),dest/n/rel)
        assert verify(dest/n)==old['kits'][n]
    for name,h in old['rcj'].items():copy(original(L/'out/rcj'/name,h),dest/'rcj'/name)
    for r in changes:
        p=dest/r['name'];assert z.sha(p)==r['baseline_sha256']
        saved=D/(label+'_before')/r['name'];saved.parent.mkdir(parents=True,exist_ok=True);p.rename(saved)
        copy(L/r['relative_path'],p)
    for n in names:assert verify(dest/n)==seals[n] and files(dest/n)==now[n]
    assert files(dest/'rcj')==rcj
    records.append(dict(base=label,files=len(changes),status='PASS',exact_bytes_modes=True))
write(D/'DELTA_REPLAY.json',dict(status='PASS',records=records,ordinary_files=len(rows),candidate_files=len(cr),optional_files=len(optional),kits=seals))
print(json.dumps(dict(status='PASS',ordinary_files=len(rows),candidate_files=len(cr),optional_files=len(optional),kits=seals)))
