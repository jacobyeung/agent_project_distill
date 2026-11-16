"""Seal the validated CPU build; all intermediate archives stay in RAM."""
from pathlib import Path
import gzip,hashlib,io,json,re,tarfile
N=Path(__file__).resolve().parent
R=N.parent/'R'
RAM=Path('/dev/shm/b07_n4')
TMP=RAM/'release01'
TMP.mkdir(exist_ok=False)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def summary(name,count):
    p=RAM/(name+'.log');s=p.read_text()
    assert re.search(r'\b'+str(count)+r' passed\b',s) and ' failed' not in s
    return dict(passed=count,log_sha256=sha(p),summary=s.strip().splitlines()[-1])
ns=summary('n_final03',79);rs=summary('r_final03',34)
(N/'out/N4_TESTS.log').write_bytes((RAM/'n_final03.log').read_bytes())
(R/'out/R2_TESTS.log').write_bytes((RAM/'r_final03.log').read_bytes())
fixtures=[]
for name in ('a30','a31','a32','a33'):
    v=json.loads((RAM/name/'RESULT.json').read_text());assert v['passed']
    fixtures.append(dict(v,path=str(RAM/name),result_sha256=sha(RAM/name/'RESULT.json'),trace_sha256=sha(RAM/(name+'.json'))))
dump(N/'out/N4_FIXTURES.json',fixtures)
rehearsals=[]
for name in ('a40','a41','a42','a43'):
    v=json.loads((RAM/name/'RESULT.json').read_text());assert v['passed']
    rehearsals.append({k:v[k] for k in ('passed','items','config_mode','phase_b_items','real_processor','boundaries')}
                      |dict(path=str(RAM/name),result_sha256=sha(RAM/name/'RESULT.json')))
dump(R/'out/R2_REHEARSALS.json',rehearsals)
validation=dict(suite=ns,reviewer_cases=5,reviewer_test_sha256=sha(N/'kit/tests/test_review_offnative.py'),
    reviewer_test_adaptation='N4_REVIEW_TEST_ADAPTATION.json',worker_fixtures=4,
    opaque_worker_fixtures=2,three_shards_one_cutoff=True,production_config_transport_only=False,
    readiness={b:{k:'NOT READY' for k in ('harness','e2e')} for b in ('revsi999t32','vsibench5130')})
dump(N/'out/N4_VALIDATION.json',validation)
dump(R/'out/R2_VALIDATION.json',dict(suite=rs,rehearsals=4,accepted_report_cases=2,
    exact_reproduction={'vsibench5130':{'score':68.77,'percentile_95':[66.5,71.0]},
                        'revsi999t32':{'score':64.94,'percentile_95':[61.3,68.4]}},
    verification='Exact equality against accepted reports for every group and all three budgets; fixed rounded B2048 values asserted by tests.',
    readiness={'vsibench5130':'NOT READY','revsi999t32':'NOT READY'},production_config_transport_only=False))
from offnative.opacity import path_name,pack,scan_members
from offnative.io import tar_bytes
packages={};name_map={};preserved={}
for key in ('vsi','revsi'):
    previous=R/'out'/('package_'+key+'.tar')
    with tarfile.open(previous) as tf:names=tf.getnames()
    names=set(names)|{'kit/xnames.py','kit/'+key+'/launcher/xnames.py','OPEN_INPUTS.md','tests/test_names.py'}
    files={name:(R/name).read_bytes() for name in sorted(names)}
    files['xnames.py']=(R/'kit/xnames.py').read_bytes()
    files['0.py']=b"import sys,xnames\nxnames.install('.')\nxnames.entry(['kit/rebind.py',*sys.argv[1:]])\n"
    name_map[key]={path_name(n):n for n in files}
    packed,pins=pack(files);assert not pins
    raw=gzip.compress(tar_bytes(packed),mtime=0)
    count=scan_members(raw)
    temp=TMP/(key+'.tar');temp.write_bytes(raw)
    old=sha(previous);backup=previous.with_name(previous.stem+'.before_r2.'+old[:12]+'.tar')
    assert not backup.exists();previous.rename(backup)
    previous.write_bytes(raw)
    packages[key]=dict(path=str(previous.relative_to(R)),bytes=len(raw),sha256=sha(previous),files=count,
        format='gzip-compressed tar',members={n:hashlib.sha256(v).hexdigest() for n,v in packed.items()})
    preserved[str(backup)]=old
    # Verify every member against its source bytes, including accepted readers and items.
    with tarfile.open(previous) as tf:
        assert {m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf}==packages[key]['members']
dump(R/'out/PACKAGE_PINS.json',packages);dump(R/'out/R2_NAME_MAP.json',name_map)
dump(R/'out/R2_ARCHIVE_CHECK.json',dict(passed=True,packages=packages,preserved=preserved))
from offnative.package import package
code_sha=package()
code=N/'out/code.tar';pins=json.loads((N/'out/CODE_PINS.json').read_text())
with tarfile.open(code) as tf:
    actual={m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf}
assert actual=={r['path']:r['sha256'] for r in pins['files']}
assert scan_members(code.read_bytes())>=len(actual)
dump(N/'out/N4_ARCHIVE_CHECK.json',dict(passed=True,sha256=code_sha,bytes=code.stat().st_size,
    members=len(actual),format='gzip-compressed tar',owner_offkit_copied=False))
dep=N/'out/DEPENDENCY_PINS.json';v=json.loads(dep.read_text())
v['scope']='Source snapshot pins; CODE_PINS.json additionally pins the exact opaque transported members.'
v['transported_files']=[r for r in pins['files'] if r['path'].startswith('d/')];dump(dep,v)
dump(N/'out/N4_RELEASE.json',dict(code_sha256=code_sha,r_packages={k:v['sha256'] for k,v in packages.items()},
    active_snapshot=json.loads((N/'vendor/ACTIVE.json').read_text()),submitted=False,uploaded=False))
(N/'out/NATIVE_KIT_READY.md').write_text(
    'ReVSI × harness: NOT READY; ReVSI × e2e: NOT READY; VSI-Bench × harness: NOT READY; VSI-Bench × e2e: NOT READY.\n\n'
    'The CPU gate passes 79 tests, including the five reviewer cases. R4 uses the real submission argv instead of its hard-coded retired export; its original hash and adaptation are recorded. Four whole-worker fixtures and two opaque-source fixtures pass. The three-shard cutoff test preserves finished primary records and reports missing IDs.\n\n'
    'Model prompts retain the direct clip metadata and bytes; only geometry carries dense slots. Both secondary decodes use the registered ThinkingBudget. Reduced harness proof requires camera equality and reports the five distance items without loading lost masks. E2E distance items are reported in every mode. Distance response equality, query digests and independent re-serving are not established.\n\n'
    'All 288 VSI-Bench media sizes are bound. A2_RESULT.json was absent, so ReVSI hashes and the real pixel check remain pending. Nine harness shards use the measured rate model and a 600-second return reserve; unmeasured costs prevent a guaranteed completion estimate.\n\n'
    'Production still needs owner-complete artifacts, the loaded-entry prompt audit, EAT-1 where applicable, and genuine transport-only rehearsals. CPU fixtures do not establish GPU logits, native-library path resolution or live namespace execution. Nothing was submitted or uploaded.\n\n'
    f'code.tar: {code.stat().st_size} bytes; SHA256 `{code_sha}`. The tar is gzip compressed. CODE_PINS.json, DEPENDENCY_PINS.json, N4_ARCHIVE_CHECK.json and SHIP_SHA256SUMS bind the release. N4_VALIDATION.json and N4_FIXTURES.json record the current CPU evidence.\n')
(R/'out/REBIND_READY.md').write_text(
    'VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.\n\n'
    'The CPU gate passes 34 tests and four rehearsals covering both benchmarks with step544 and D0-style staging. Accepted report reproduction is exact: VSI-Bench 68.77 [66.5, 71.0]; ReVSI 64.94 [61.3, 68.4]. Tests also compare every group and all three budgets.\n\n'
    'Accepted reader, scorer and item bytes remain identical. Packed paths, runtime environment boundaries, submission names and text diagnostics use opaque spellings. Nested member scans and actual submission scans pass. The 288 media sizes bind the existing hashes; staging still verifies media.\n\n'
    'Production requires the owner selection/export inputs and live runtime validation. The CPU stand-ins do not establish GPU or namespace compatibility. Nothing was submitted or uploaded.\n\n'+
    '\n'.join(f"{key}: {v['bytes']} bytes; SHA256 `{v['sha256']}`." for key,v in packages.items())+
    '\n\nR2_VALIDATION.json, R2_REHEARSALS.json, R2_ARCHIVE_CHECK.json, PACKAGE_PINS.json and SHIP_SHA256SUMS record the evidence. Packages are gzip-compressed tar files.\n')
# Keep the stale forced-response historical receipt as a clearly named prior artifact.
p=N/'out/PROOF_CPU.json'
if p.exists():p.rename(N/'out/PROOF_CPU.before_n4.json')
dump(N/'out/PROOF_CPU.json',dict(status='CPU synthetic proof-policy tests passed; original-export replay not run',
    required_camera_items=5,reported_distance_items=5,distance_cache_loaded=False,
    distance_served_response_requirement=False,model_logit_equality_established=False,
    evidence='N4_VALIDATION.json'))
print(json.dumps({'N':code_sha,'R':{k:v['sha256'] for k,v in packages.items()}},sort_keys=True))
