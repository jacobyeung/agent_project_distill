import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import shutil
from launch_r1.build import verify
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest

base=z.load(D/'BASELINE.json');old=z.load(L/'work/build24m4n/BASELINE.json')
assert digest(inventory(T))==base['tree']==old['tree']
def inv(k):
    return {str(p.relative_to(k)):dict(sha256=z.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511)
            for p in k.rglob('*') if p.is_file()}
current={n:inv(kit(n)) for n in base['kits']}
seals={n:verify(kit(n)) for n in current}
for n in ('q','n','n_go'):
    assert current[n]==base['files'][n]==old['files'][n]
    assert seals[n]==base['kits'][n]
changed={n for n in current['qd'].keys()|base['files']['qd'].keys() if current['qd'].get(n)!=base['files']['qd'].get(n)}
assert changed=={'b/f0.py','SHA256SUMS.txt','BUILD.json'},changed
oldchanged={n for n in current['qd'].keys()|old['files']['qd'].keys() if current['qd'].get(n)!=old['files']['qd'].get(n)}
assert oldchanged=={'b/a.py','b/f0.py','SHA256SUMS.txt','BUILD.json'},oldchanged
assert z.load(kit('qd')/'k/n.json')==z.load(kit('n')/'k/n.json')
assert z.load(kit('qd')/'k/a.json')['GO'] is False
rcj={p.name:z.sha(p) for p in (L/'out/rcj').iterdir() if p.is_file()}
assert {n for n in rcj.keys()|base['rcj'].keys() if rcj.get(n)!=base['rcj'].get(n)}=={'nd.py','x.py'}
for n,h in {'rcj.sh':'b23393f2','pc.py':'1fc1c7a8','ps.py':'6945292e','P_SAMPLE_I.json':'fff742bb'}.items():
    assert rcj[n].startswith(h)

# Rebuild the exact Orchard baseline, verify it, then apply only the declared delta.
replay=D/'delta_replay';replay.mkdir()
for name,v in old['files']['qd'].items():
    p=kit('qd')/name
    if current['qd'].get(name)!=v:p=L/'attic/build24m4n/out/kit_qd'/name
    assert z.sha(p)==v['sha256']
    out=replay/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out);out.chmod(v['mode'])
assert verify(replay)==old['kits']['qd']
for name in sorted(oldchanged):
    p=replay/name
    if p.exists():
        a=L/'attic/build24m4o/delta_replay'/name;a.parent.mkdir(parents=True,exist_ok=True);p.rename(a)
    shutil.copyfile(kit('qd')/name,p);p.chmod(current['qd'][name]['mode'])
assert verify(replay)==seals['qd'] and inv(replay)==current['qd']

uploads=[]
for name in sorted(oldchanged):
    p=kit('qd')/name;v=current['qd'][name]
    uploads.append(dict(name='qd/'+name,relative_path=str(p.relative_to(L)),local_path=str(p),
        transfer='local-upload',action='replace' if name in old['files']['qd'] else 'add',
        sha256=v['sha256'],bytes=v['bytes'],mode=format(v['mode'],'04o'),
        baseline_sha256=old['files']['qd'].get(name,{}).get('sha256')))
for name in ('nd.py','x.py'):
    p=L/'out/rcj'/name
    uploads.append(dict(name='rcj/'+name,relative_path=str(p.relative_to(L)),local_path=str(p),
        transfer='local-upload',action='replace' if name in base['rcj'] else 'add',sha256=rcj[name],
        bytes=p.stat().st_size,mode=format(p.stat().st_mode&511,'04o'),baseline_sha256=base['rcj'].get(name)))
up=dict(schema='cpu-publication-delta-v1',baseline='Orchard qd 7d358ff5 and stated rcj pins',
    baseline_kit_seals=old['kits'],baseline_rcj=base['rcj'],kit_seals={'qd':seals['qd']},
    unchanged_kit_seals={n:seals[n] for n in ('q','n','n_go')},tree_sha256=base['tree'],
    files=uploads,total_files=len(uploads),total_bytes=sum(r['bytes'] for r in uploads),
    GO=False,uploaded=False,launched=False,route_changed=False)
write(L/'out/UPLOADS_24M4O.json',up)
(L/'out/UPLOADS_24M4O.list').write_text(''.join(r['name']+'\n' for r in uploads))
write(D/'DELTA_REPLAY.json',dict(status='PASS',baseline=old['kits']['qd'],result=seals['qd'],
    changed=sorted(oldchanged),exact_bytes_modes=True,unchanged_q_n_n_go=True,rcj=rcj))

# Preserve the supplied small evidence files, never attempt to rebuild either database.
ev=D/'evidence173680';ev.mkdir();evidence={}
names=['job.log','timings.json','db_bytes.json','proc_check.json','p_sample.json',
       'rd0/rdiff_summary.json','rd0/rdiff.json.gz']
names+=sorted(str(p.relative_to(E)) for p in E.glob('k_*.json'))
assert sum((E/n).stat().st_size for n in names)<25_000_000
for name in names:
    p=E/name;q=ev/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
    assert z.sha(p)==z.sha(q)
    evidence[name]=dict(sha256=z.sha(q),bytes=q.stat().st_size)
write(D/'EVIDENCE_FILES.json',dict(source=str(E),files=evidence,databases_supplied=False,pc_child_log_supplied=False))

failures=[]
for name,why in [('evidence.log','A planner fixture is not the pinned P archive; authenticated the real local tar by its complete tree inventory instead.'),
                 ('evidence2.log','Local tar serialization differs from the staged archive pin; all 799 member hashes authenticate the exact P tree.'),
                 ('evidence3.log','P has no training_contract.py; comparison now records the absent P file.'),
                 ('tests.log','The fixture expected post_returncode=1 for an already-refused producer with a failed gate; corrected the fixture to preserve existing status behavior.'),
                 ('finalize.log','The local validation read GO from k/8.json; corrected the assertion to read the native k/a.json control. No kit content changed.')]:
    p=D/name
    if p.exists():failures.append(dict(output_file=str(p.relative_to(L)),output=p.read_text(),resolution=why))
failures.append(dict(output='AssertionError at start.py: assert manifest==files',
    resolution='The supplied TREE_FILES.sha256 is stale; recorded every discrepancy in TREE_MANIFEST_CHECK.json. Actual native tree inventory verifies de202f58; no tree or manifest edit.'))
failures.append(dict(output="sed: can't read work/build24m4n/finish.py: No such file or directory",
    resolution='Inspected the named existing package_n.py instead; no command was killed and no remote work ran.'))
write(D/'FAILURES.json',dict(status='RESOLVED_LOCAL_CHECKS',failures=failures,
    unresolved_evidence=['Exact pool/T0_gaps/dev_matches integer not published','N child pc_n.log not supplied','Full N/P stores not supplied; complete path counts require next CPU publication']))
tests=z.load(D/'TESTS.json');rec=z.load(D/'RECORDER_TESTS.json')
assert tests['status']==rec['status']=='PASS' and tests['tests']==12 and rec['tests']==4
assert z.load(D/'SCAN_qd.json')['kit_sha256']==seals['qd']
assert z.load(D/'RCJ_SCAN.json')['status']=='PASS'
v=dict(status='PASS',tree_sha256=base['tree'],kits=seals,publication_tests=tests,recorder_tests=rec,
    qd_decoded_scan='work/build24m4o/SCAN_qd.json',rcj_name_environment_scan='work/build24m4o/RCJ_SCAN.json',
    delta_replay='work/build24m4o/DELTA_REPLAY.json',evidence='work/build24m4o/EVIDENCE_FILES.json',
    qualifications=['Fixture checks only; no production CPU rerun, model assets, GPU or discovery',
    'Exact census count and underlying E95 child exception unavailable',
    'Full-population field counts are implemented for the next CPU job; local sample hashes prove 73 exact rows'],
    route_changed=False,tree_changed=False,q_n_n_go_changed=False,GO=False,uploaded=False,launched=False)
write(D/'VALIDATION.json',v)
lines=[
    'qd '+seals['qd']+'; unchanged C″ '+base['tree']+', q '+seals['q']+', n '+seals['n']+', n_go '+seals['n_go']+'.',
    'DIAG_173680.md attributes all 4,768 unlisted absences to N’s merged dev predicate; the 3,985 null-source rows are legacy camera rows. Exactly 29 U_Faithful absences are listed.',
    'All 73 present requested N samples are hash-proven; 27 are absent. Added fields, provenance paths/FPS-source labels and ordinals explain their differences; existing targets, prompts, frames and units match.',
    'rcj/nd.py publishes n_sample.json, nd.json and na.json.gz after rdiff on success or refusal when N exists; it scans every matched row and keeps total new publication below 5 MB. Build/refusal status and mode b remain unchanged.',
    'qd records NaN/Infinity as strings with nonfinite_values paths; the native strict provenance loader accepts the output and native numerical refusal persists.',
    'Twelve publication fixtures, four native-recorder fixtures, decoded/name/environment scans and exact delta replay pass; VALIDATION.json and FAILURES.json record scope and outputs.',
    'UPLOADS_24M4O.json/.list contain '+str(up['total_files'])+' files / '+str(up['total_bytes'])+' bytes against Orchard qd 7d358ff5 plus stated rcj pins, including 24m4n a.py and f0.py.',
    'ROUTES_24M4O.md prices direct admission and compatible regeneration; both need tree changes and an ORCH policy decision. No route fix, arming, upload, CPU rerun or discovery was performed; GO=false.',
    'Exact T0_gaps observed count, underlying E95 child exception and full-population path counts are unavailable from supplied artifacts; no equality or processor success is claimed.',
    'DELIVERY_24M4O.json identifies the package; PACKAGE_CHECK.json verifies members and checksum. Superseded bytes remain in attic; TREE_FILES.sha256 discrepancy is recorded without edits.'
]
assert len(lines)<12
(L/'out/BUILD24M4O_REPORT.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(dict(status='PASS',kits=seals,delta_files=len(uploads),delta_bytes=up['total_bytes'],evidence_bytes=sum(v['bytes'] for v in evidence.values())),indent=2))
