from pathlib import Path
import datetime,gzip,hashlib,io,json,sys,tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24g'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
baseline=J.load(D/'BASELINE.json')
tree=inventory(L/'work/tree_r1')
assert tree==baseline['tree']==J.load(L/'work/build24f/TREE_FILES.json')
assert digest(tree)=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
for n,h in baseline['packages'].items():assert J.sha(L/'out'/n)==h
assert J.sha(L/'out/SESSION_NAMES_24F.json')==baseline['session_names']
kits={n:L/('out/kit_n_go' if n=='n_go' else 'work/build24/kits/'+n) for n in ('q','n','n_go')}
seals={};changes={}
for n,k in kits.items():
    seals[n]=verify(k)
    current={str(p.relative_to(k)):J.sha(p) for p in k.rglob('*') if p.is_file()}
    changes[n]=[f for f in sorted(set(current)|set(baseline['kits'][n])) if current.get(f)!=baseline['kits'][n].get(f)]
    assert changes[n]==([] if n=='q' else ['BUILD.json','SHA256SUMS.txt','b/pc.py'])
    assert J.load(k/'k/a.json')['GO']==(n=='n_go')
    scan=J.load(D/('SCAN_'+n+'.json'))
    assert scan['status']=='PASS' and scan['kit_seal']==seals[n]
assert not (kits['q']/'b/pc.py').exists() and 'b/pc.sh' not in (kits['q']/'job.sh').read_text()
assert len({J.sha(p) for p in [D/'live.py',L/'work/build24f/live.py',kits['n']/'b/pc.py',kits['n_go']/'b/pc.py']})==1
for n in ('KIT_TESTS','NAMING_TESTS','RESOLVER_TESTS'):assert J.load(D/(n+'.json'))['successful']
for n in ('LIVE_TESTS','RUNTIME_TESTS'):assert J.load(D/(n+'.json'))['passed']
for n in ('COPIER_TESTS','EXTRA_COPIER_TESTS'):assert J.load(D/(n+'.json'))['status']=='PASS'
assert all(v['returncode']==0 for v in J.load(D/'SUITES.json'))
assert all(v['returncode']==0 for v in J.load(D/'VALIDATION.json'))
up=J.load(L/'out/UPLOADS_24G.json')
assert [r['name'] for r in up['files']]==['n/BUILD.json','n/SHA256SUMS.txt','n/b/pc.py']
for row in up['files']:assert J.sha(row['local_path'])==row['sha256']
for row in J.load(L/'out/UPLOADS_24G_GO.json')['files']:assert J.sha(row['local_path'])==row['sha256']
sessions_path=J.load(kits['n']/'k/p.json')['n_root']+'/n_s/sess.json'
assert sessions_path.startswith('/project/')
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=digest(tree),tree_files=len(tree),changed_kit_files=changes,kits=seals,existing_packages_unchanged=True,session_names_unchanged=True,sessions_path=sessions_path,GO_only_in_n_go=True,fixture_values_excluded_from_package=True))
card=L/'out/N_CARD_KIT_ROWS.md';text=card.read_text()
for n in ('n','q','n_go'):
    old=J.load(L/'out/DELIVERY_24F.json')['kits'][n];text=text.replace(old,seals[n])
text=text.replace('work/build24f/KIT.json and out/UPLOADS_24F_GO.json','work/build24g/INVARIANTS.json and out/UPLOADS_24G_GO.json')
needle='SESSION_NAMES_24F.json fixes milestone names plus three once-claimed stop generations. Without sessions, the tar and an explicit marker remain local.'
text=text.replace(needle, 'SESSION_NAMES_24F.json fixes unchanged milestone names plus three once-claimed stop generations.\nThe copier reads `'+sessions_path+'` outside the kit, ignoring TK_KIT_HOME; --sessions PATH explicitly overrides it.\nThe sessions directory must belong to the job user with mode 0700; sess.json must be a regular non-symlink file with mode 0600 and a JSON object mapping part names to URLs.\nAn unusable sessions file records `export not uploaded: sessions unusable (<reason>)`, uploads nothing, and keeps the tar node-local. The private node-local copy has mode 0600.')
old=L/'attic/build24g/out/N_CARD_KIT_ROWS.md';old.parent.mkdir(parents=True,exist_ok=True);card.rename(old);card.write_text(text)
report=[
'BUILD24G PASS. The kit-only copier fix is packaged; normal kits remain GO=false.',
'Tree: '+digest(tree)+'; all '+str(len(tree))+' files are byte-identical to build 24f (work/build24g/INVARIANTS.json).',
'Kit n: '+seals['n']+'; kit q: '+seals['q']+'.',
'GO variant: '+seals['n_go']+'; it is not authorized for upload.',
'Kit n and kit_n_go run the copier. Kit q has no copier; resealing it preserves its seal and bytes.',
'Default sessions file: '+sessions_path+'; k/p.json supplies n_root, independently of the live-output target.',
'TK_KIT_HOME is ignored. --sessions PATH selects an explicit file; the existing explicit home API remains supported.',
'The directory must be owned by the job user with mode 0700. The file must be regular, non-symlink, mode 0600, and a JSON object mapping part names to HTTP(S) URLs.',
'Opened directory/file descriptors prevent symlink replacement; validation failures use fixed reason text and upload nothing.',
'The private node-local directory/file use 0700/0600. Writer stdout and stderr are discarded; no session value enters live evidence or reports.',
'Copier evidence: five failing-before controls, thirteen passing-after cases, and an explicit CLI success (work/build24g/COPIER_TESTS.json).',
'Late mint, writer failure redaction, complete four-part mapping, directory symlink and missing-directory tests pass (EXTRA_COPIER_TESTS.json).',
'Decoded q/n/GO scans and kit, naming, resolver and guard suites pass (work/build24g/SCAN_*.json, SUITES.json and VALIDATION.json).',
'Live-copy tests pass, including TERM, byte cap, idempotence, stop generations and checkpoint fallback; runtime tests pass (LIVE_TESTS.json and RUNTIME_TESTS.json).',
'SESSION_NAMES_24F.json is byte-identical; no SESSION_NAMES_24G.json is needed. The card supplies the authoritative sessions location and modes.',
'Upload delta after 24f: '+str(up['total_files'])+' files, '+str(up['total_bytes'])+' bytes; stream root work/build24g/upload; out/UPLOADS_24G.list names the files.',
'out/UPLOADS_24G_GO.json contains only the three-file GO delta against kit n and is not authorized for upload.',
'The tree, configs, admission, legality, removals, opener rows, step-544 lineage, resolver identity checks and DEFERRED boundary remain unchanged.',
'Existing packages remain unchanged. No rehearsal path was opened or modified, and go_rehearsal.sh was not run; no distributed result is claimed.',
'out/DELIVERY_24G.json records the package path, SHA-256, bytes and verified member seal. Evidence paths without a prefix are under work/build24g.'
]
assert len(report)<25
(L/'out/BUILD24G_REPORT.md').write_text('\n'.join(report)+'\n')
# Select only sources and value-free evidence; never include test session files.
selected={}
def add(p):
    if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in tree:add(L/'work/tree_r1'/name)
for k in kits.values():
    for p in k.rglob('*'):add(p)
for root in (D/'upload',D/'scanners'):
    for p in root.rglob('*'):add(p)
for p in D.iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json','.log') and p.name not in ('PACKAGE_MANIFEST.json','package.log'):add(p)
for folder in ('guard_q','guard_n'):
    for p in (D/folder).glob('*.json'):add(p)
for name in ('out/UPLOADS_24G.json','out/UPLOADS_24G.list','out/UPLOADS_24G_GO.json','out/BUILD24G_REPORT.md','out/N_CARD_KIT_ROWS.md','out/SESSION_NAMES_24F.json','out/DELIVERY_24F.json','out/TREE_SEAL.json','out/TREE_FILES.sha256','work/build24f/live.py','work/build24/joblib.py'):
    add(L/name)
manifest={n:dict(bytes=p.stat().st_size,sha256=J.sha(p)) for n,p in sorted(selected.items())}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
base=J.load(L/'out/DELIVERY_24F.json')
record=dict(schema='build24g-overlay-v1',package_seal=seal,base=dict(path=base['package'],sha256=base['sha256']),files=manifest,tree_sha256=digest(tree),kits=seals)
J.write(D/'PACKAGE_MANIFEST.json',record);add(D/'PACKAGE_MANIFEST.json')
target=L/'out'/('tree_rebuild_b24g_'+seal[:8]+'.tar')
seen={}
with target.open('xb') as f,gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w|') as t:
    for name,p in sorted(selected.items()):
        raw=p.read_bytes();info=tarfile.TarInfo(name);info.mode=0o755 if name.endswith('.sh') else 0o644
        h=hashlib.sha256(raw).hexdigest()
        if h in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[h];t.addfile(info)
        else:seen[h]=name;info.size=len(raw);t.addfile(info,io.BytesIO(raw))
expected={n:J.sha(p) for n,p in selected.items()}
with tarfile.open(target) as t:
    assert {m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in t}==expected
delivery=dict(status='PACKAGED',package=str(target.relative_to(L)),bytes=target.stat().st_size,sha256=J.sha(target),package_seal=seal,verified_members=len(selected),base=record['base'],tree=dict(tree_sha256=digest(tree),files=len(tree)),kits=seals,GO=False,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sessions_path=sessions_path,uploads=dict(files=up['total_files'],bytes=up['total_bytes']),checks='PASS',rehearsal='UNTOUCHED')
J.write(L/'out/DELIVERY_24G.json',delivery)
print(json.dumps(delivery,indent=2))
