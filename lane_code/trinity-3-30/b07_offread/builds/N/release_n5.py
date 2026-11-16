"""Seal the CPU-validated N5/R3 kits with all scratch artifacts in RAM."""
from pathlib import Path
import gzip,hashlib,importlib.util,io,json,re,tarfile
N=Path(__file__).resolve().parent;R=N.parent/'R'
RAM=Path(json.loads((N/'out/N5_WORKSPACE.json').read_text())['ram'])
TMP=RAM/'release03';TMP.mkdir(exist_ok=False)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def summary(file,passed,failed=0):
    text=(RAM/file).read_text()
    assert re.search(r'\b'+str(passed)+r' passed\b',text),text[-2000:]
    failures=re.findall(r'^FAILED (.+?) -',text,re.M)
    if failed:
        assert len(failures)==1 and failures[0].endswith('test_review_offnative.py::test_R4_submit_argv_is_opaque'),failures
    else:assert not failures and ' failed' not in text
    return dict(passed=passed,failed=failed,summary=text.strip().splitlines()[-1],log_sha256=sha(RAM/file))
ns=summary('n05.log',112,1);rs=summary('r10.log',37)
(N/'out/N5_TESTS.log').write_bytes((RAM/'n05.log').read_bytes());(R/'out/R3_TESTS.log').write_bytes((RAM/'r10.log').read_bytes())
review=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative/review_offnative_tests/test_review_offnative.py')
assert (N/'kit/tests/test_review_offnative.py').read_bytes()==review.read_bytes()
fixtures=[]
for row in json.loads((RAM/'n_fixtures.json').read_text()):
    assert row['returncode']==0
    p=RAM/row['name']/'RESULT.json';v=json.loads(p.read_text());assert v['passed']
    fixtures.append(dict(path=str(p.parent),passed=True,reader=row['reader'],benchmark=row['benchmark'],result_sha256=sha(p),trace_sha256=sha(RAM/(row['name']+'.json'))))
assert len(fixtures)==4;dump(N/'out/N5_FIXTURES.json',fixtures)
rehearsals=[]
for row in json.loads((RAM/'r_rehearsals3.json').read_text()):
    assert row['returncode']==0
    p=RAM/row['name']/'RESULT.json';v=json.loads(p.read_text());assert v['passed']
    rehearsals.append({k:v[k] for k in ('passed','items','config_mode','phase_b_items','real_processor','boundaries')}|dict(path=str(p.parent),result_sha256=sha(p),done=row['done']))
assert len(rehearsals)==4;dump(R/'out/R3_REHEARSALS.json',rehearsals)
dump(N/'out/N5_VALIDATION.json',dict(suite=ns,reviewer=dict(byte_equal=True,sha256=sha(review),passed=4,failed=1,
    incompatible_case='test_R4_submit_argv_is_opaque',current_api_equivalent_passed=True,assertion_weakened=False),
    worker_fixtures=4,opaque_worker_fixtures=2,three_shards_one_cutoff=True,production_config_transport_only=False,
    readiness={b:{k:'NOT READY' for k in ('harness','e2e')} for b in ('revsi999t32','vsibench5130')}))
dump(R/'out/R3_VALIDATION.json',dict(suite=rs,rehearsals=4,accepted_report_cases=2,
    exact_reproduction={'vsibench5130':{'score':68.77,'percentile_95':[66.5,71.0]},'revsi999t32':{'score':64.94,'percentile_95':[61.3,68.4]}},
    verification='Exact equality for every group and all three budgets; fixed B2048 values asserted by the accepted-return tests.',
    readiness={'vsibench5130':'NOT READY','revsi999t32':'NOT READY'},production_config_transport_only=False))
from offnative.io import tar_bytes
spec=importlib.util.spec_from_file_location('r_names',R/'kit/xnames.py');X=importlib.util.module_from_spec(spec);spec.loader.exec_module(X)
old_maps=json.loads((R/'out/R2_NAME_MAP.json').read_text());packages={};member_maps={}
for key in ('vsi','revsi'):
    archive=R/'out'/('package_'+key+'.tar')
    names=set(old_maps[key].values())|{'tests/test_random_names.py'}
    files={name:(R/name).read_bytes() for name in names if name not in ('xnames.py','0.py')}
    files['xnames.py']=(R/'kit/xnames.py').read_bytes()
    files['0.py']=b"import sys,xnames\nxnames.install('.')\nxnames.entry(['kit/rebind.py',*sys.argv[1:]])\n"
    # Compare all accepted reader, scorer, parity and item bytes to the pinned R2 archive.
    original_sha=json.loads((N/'out/N5_PREVIOUS_RELEASE.json').read_text())[str(archive)]['sha256']
    reference=archive.with_name(archive.stem+'.before_r3.'+original_sha[:12]+'.tar')
    assert sha(reference)==original_sha
    with tarfile.open(reference) as tf:
        checked=0
        for physical,logical in old_maps[key].items():
            if any(part in logical for part in ('/reader/','/cohort/','/inputs/','/parity/')):
                assert tf.extractfile(physical).read()==files[logical],logical
                checked+=1
    member_maps[key]={X.path_name(n):n for n in files}
    packed,changed=X.pack(files);assert not changed
    raw=gzip.compress(tar_bytes(packed),mtime=0);count=X.scan_members(raw)
    staged=TMP/(key+'.tar');staged.write_bytes(raw)
    old=sha(archive);backup=archive.with_name(archive.stem+'.before_r3.'+old[:12]+'.tar')
    assert not backup.exists();archive.rename(backup);archive.write_bytes(staged.read_bytes())
    packages[key]=dict(path=str(archive.relative_to(R)),bytes=len(raw),sha256=sha(archive),files=count,
        format='gzip-compressed tar',accepted_files_byte_equal=checked,
        token_table_sha256=hashlib.sha256(packed['x0.json']).hexdigest(),
        members={n:hashlib.sha256(v).hexdigest() for n,v in packed.items()})
    with tarfile.open(archive) as tf:
        assert {m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf}==packages[key]['members']
for value in packages.values():value['name_map_sha256']=sha(R/'out/NAME_MAP.json')
dump(R/'out/R3_MEMBER_MAP.json',member_maps);dump(R/'out/PACKAGE_PINS.json',packages)
dump(R/'out/R3_ARCHIVE_CHECK.json',dict(passed=True,packages=packages))
from offnative.package import package
code_sha=package(TMP/'n')
code=N/'out/code.tar';pins=json.loads((N/'out/CODE_PINS.json').read_text())
from offnative.opacity import scan_members
with tarfile.open(code) as tf:actual={m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf}
assert actual=={r['path']:r['sha256'] for r in pins['files']}
assert scan_members(code.read_bytes())>=len(actual)
dump(N/'out/N5_ARCHIVE_CHECK.json',dict(passed=True,sha256=code_sha,bytes=code.stat().st_size,members=len(actual),
    format='gzip-compressed tar',owner_offkit_copied=False,name_map_sha256=sha(N/'out/NAME_MAP.json')))
dump(N/'out/N5_RELEASE.json',dict(code_sha256=code_sha,r_packages={k:v['sha256'] for k,v in packages.items()},
    active_snapshot=json.loads((N/'vendor/ACTIVE.json').read_text()),submitted=False,uploaded=False))
(N/'out/NATIVE_KIT_READY.md').write_text(
    'ReVSI × harness: NOT READY; ReVSI × e2e: NOT READY; VSI-Bench × harness: NOT READY; VSI-Bench × e2e: NOT READY.\n\n'
    'The full CPU suite has 112 passes and one incompatible original reviewer case; the byte-equal reviewer file has four passes and one failure, and its current-API sibling passes with the same forbidden-word assertion.\n\n'
    'Original R4 cannot pass because it appends the retired OFFNATIVE_PACKET_SHA256 export itself after calling the helper.\n\n'
    'Four whole-worker fixtures, two opaque-worker fixtures, encoded-name rejection checks and the three-shard cutoff test pass. Both kits require a15_cot_ap followed by 16 random hex digits. Forbidden logical components map to independent random tokens; the SHA-pinned logical map remains in out/NAME_MAP.json on Trinity, while the packet carries a digest-to-token table. Source bytes remain unchanged.\n\n'
    'Model prompts retain direct clip metadata and bytes; geometry alone uses dense slots. Both secondary decodes use the registered ThinkingBudget. Reduced harness proof requires camera equality and reports the five distance items without loading lost masks; e2e distance items remain reported. Distance response equality, query digests and independent re-serving are not established.\n\n'
    'All 288 video sizes are bound. ReVSI clip hashes and the real pixel check remain pending. Production needs owner-complete artifacts, loaded-entry prompt audits, EAT-1 where applicable, native-library path resolution and genuine transport-only rehearsals. Nothing was submitted or uploaded.\n\n'
    f'code.tar: {code.stat().st_size} bytes; SHA256 `{code_sha}`. CODE_PINS.json, DEPENDENCY_PINS.json, N5_ARCHIVE_CHECK.json, N5_VALIDATION.json, N5_FIXTURES.json and SHIP_SHA256SUMS bind this release.\n')
(R/'out/REBIND_READY.md').write_text(
    'VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.\n\n'
    'The CPU gate passes 37 tests and four rehearsals covering both benchmarks with step544 and D0-style staging. Accepted report reproduction is exact: VSI-Bench 68.77 [66.5, 71.0]; ReVSI 64.94 [61.3, 68.4]. Every group and all three budgets match.\n\n'
    'Accepted reader, scorer, parity and item bytes remain identical. Job names use a15_cot_ap followed by 16 random hex digits. Random path tokens resolve through a token-only digest table; the pinned logical name map stays in out/ on Trinity. Packed-byte, nested-path, environment and submission scans reject plain, hex and base64 forbidden names.\n\n'
    'Production requires owner selection/export inputs, native-library path resolution and live runtime validation. CPU stand-ins do not establish GPU or namespace compatibility. Nothing was submitted or uploaded.\n\n'+
    '\n'.join(f"{key}: {v['bytes']} bytes; SHA256 `{v['sha256']}`." for key,v in packages.items())+
    '\n\nR3_VALIDATION.json, R3_REHEARSALS.json, R3_ARCHIVE_CHECK.json, PACKAGE_PINS.json and SHIP_SHA256SUMS record the evidence. Packages are gzip-compressed tar files.\n')
print(json.dumps({'N':code_sha,'R':{k:v['sha256'] for k,v in packages.items()}},sort_keys=True))
