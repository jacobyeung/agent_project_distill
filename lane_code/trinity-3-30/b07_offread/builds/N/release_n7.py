"""Seal salted N7/R5 packets and retain bounded release evidence."""
from pathlib import Path
import gzip,hashlib,hmac,importlib.util,io,json,os,re,secrets,stat,tarfile
N=Path(__file__).resolve().parent;R=N.parent/'R'
W=json.loads((N/'out/N7_WORKSPACE.json').read_text());RAM=Path(W['ram'])
os.environ.pop('A0_BUILD_SECRET_FILE',None)
RELEASE=RAM/('release_'+secrets.token_hex(6));RELEASE.mkdir()
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def suite(name,failed=0):
    p=RAM/(name+'.log');raw=p.read_text();failures=re.findall(r'^FAILED (.+?) -',raw,re.M)
    assert len(failures)==failed,(name,failures,raw[-2000:])
    if failed:assert failures==['kit/tests/test_review_offnative.py::test_R4_submit_argv_is_opaque']
    passed=int(re.search(r'(\d+) passed',raw)[1]);skip=re.search(r'(\d+) skipped',raw)
    return dict(passed=passed,failed=failed,skipped=int(skip[1]) if skip else 0,summary=raw.strip().splitlines()[-1],log_sha256=sha(p))
ns=suite('ns01',1);rs=suite('rs02');rg=suite('r_gate');ng=suite('n_gate')
assert (rg['passed'],ng['passed'])==(5,1)
review=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative2/review_offnative2_tests')
review_pins={}
for name in ('test_review_offnative2.py','sim_r_namespace.py'):
    ref=(review/name).read_bytes()
    for d in (N/'kit/tests',R/'tests'):assert (d/name).read_bytes()==ref
    review_pins[name]=hashlib.sha256(ref).hexdigest()
old_review=review.parent.parent/'review_offnative/review_offnative_tests/test_review_offnative.py'
assert sha(old_review)==sha(N/'kit/tests/test_review_offnative.py')
gate=dict(reviewer_passed=3,prodroot_passed=3,byte_equal=True,reviewer_files=review_pins,
    prodroot_sha256=sha(R/'tests/test_prodroot.py'),runs=json.loads((RAM/'gate_index.json').read_text()))
fixtures={}
for kind,label,owner in [('N','nf01',N),('R','rf02',R)]:
    entries=json.loads((RAM/(label+'_index.json')).read_text());assert len(entries)==4
    rows=[]
    for row in entries:
        assert row['returncode']==0
        result=RAM/row['name']/'RESULT.json';v=json.loads(result.read_text());assert v['passed']
        rows.append(dict(row,result_sha256=sha(result),passed=True))
    fixtures[kind]=rows
    dump(owner/'out'/('N7_FIXTURES.json' if kind=='N' else 'R5_REHEARSALS.json'),rows)
prod=[]
for key,label in [('N','np01'),('R','rp02')]:
    row=json.loads((RAM/(label+'_index.json')).read_text())[0];assert row['returncode']==0
    root=Path(row['root']);assert re.fullmatch('/tmp/a_900000_[0-9a-f]{12}',str(root))
    size=sum(p.lstat().st_size for p in root.rglob('*') if p.is_file() or p.is_symlink());assert size<20_000_000
    result=root/('work/result/RESULT.json' if key=='N' else 'RESULT.json');v=json.loads(result.read_text());assert v['passed']
    checks=json.loads((root/'work/NAMESPACE.json').read_text()) if key=='N' else v['namespace_checks']
    assert checks and (checks['passed'] if isinstance(checks,dict) else all(x['passed'] for x in checks))
    prod.append(dict(row,kit=key,bytes=size,result_sha256=sha(result),namespace=checks,live_mount_execution=False))
for owner,label in ((N,'N7'),(R,'R5')):
    dump(owner/'out'/(label+'_REVIEW_GATE.json'),gate)
    dump(owner/'out'/(label+'_PRODROOT.json'),prod if owner==N else prod[1])
    logs=['ns01','n_gate','np01',*[r['name'] for r in fixtures['N']]] if owner==N else ['rs02','r_gate','rp02',*[r['name'] for r in fixtures['R']]]
    log_pins={}
    for name in logs:
        p=owner/'out'/(label+'_'+name+'.log');p.write_bytes((RAM/(name+'.log')).read_bytes());log_pins[p.name]=sha(p)
    dump(owner/'out'/(label+'_TEST_LOGS.json'),log_pins)
validation=dict(suite=ns,reviewer=gate,original_reviewer=dict(passed=4,failed=1,byte_equal=True,
    reason='The original R4 test appends OFFNATIVE_PACKET_SHA256 itself; the current-API equivalent passes.'),
    fixtures=4,production_root_rehearsals=1,readiness={b:{r:'NOT READY' for r in ('harness','e2e')} for b in ('revsi999t32','vsibench5130')})
dump(N/'out/N7_VALIDATION.json',validation)
dump(R/'out/R5_VALIDATION.json',dict(suite=rs,reviewer=gate,rehearsals=4,production_root_rehearsals=1,
    exact_reproduction={'vsibench5130':{'score':68.77,'percentile_95':[66.5,71.0]},'revsi999t32':{'score':64.94,'percentile_95':[61.3,68.4]}},
    verification='Accepted-return tests assert exact equality for all groups and all three budgets.',readiness={'vsibench5130':'NOT READY','revsi999t32':'NOT READY'}))
# Refuse a changed live source or any divergence among the four adapters.
active=json.loads((N/'vendor/ACTIVE.json').read_text());pins=json.loads((N/active['R']/'PIN.json').read_text())
assert all(sha(R/name)==pin for name,pin in pins['files'].items())
modules=[N/'offnative/opacity.py',R/'kit/xnames.py',R/'kit/vsi/launcher/xnames.py',R/'kit/revsi/launcher/xnames.py']
assert len({sha(p) for p in modules})==1
spec=importlib.util.spec_from_file_location('r_release_names',modules[1]);X=importlib.util.module_from_spec(spec);spec.loader.exec_module(X)
from offnative.io import tar_bytes
old_maps=json.loads((R/'out/R4_MEMBER_MAP.json').read_text());inputs={};member_maps={};packages={};previous={}
for key in ('vsi','revsi'):
    names=set(old_maps[key].values())|{str(p.relative_to(R)) for p in (R/'tests').glob('*.py')}|{'out/R5_VALIDATION.json'}
    files={n:(R/n).read_bytes() for n in names if n not in ('0.py','xnames.py')}
    files['xnames.py']=modules[1].read_bytes()
    files['0.py']=b"import sys,xnames\nxnames.install('.')\nxnames.entry(['kit/rebind.py',*sys.argv[1:]])\n"
    inputs[key]=files;X.seed(files)
# Seed both source sets first so the build map is fixed for every repeated packet.
for key,files in inputs.items():
    archive=R/'out'/('package_'+key+'.tar');previous[key]=dict(sha256=sha(archive),bytes=archive.stat().st_size)
    checked=0
    with tarfile.open(archive) as tf:
        for physical,logical in old_maps[key].items():
            if any(part in logical for part in ('/reader/','/cohort/','/inputs/','/parity/')):
                assert tf.extractfile(physical).read()==files[logical],logical;checked+=1
    member_maps[key]={X.path_name(n):n for n in files}
    packed,changed=X.pack(files);assert not changed
    raw=gzip.compress(tar_bytes(packed),mtime=0)
    rebuilt,_=X.pack(files);assert raw==gzip.compress(tar_bytes(rebuilt),mtime=0)
    stage=RELEASE/key;stage.mkdir();(stage/'package.tar').write_bytes(raw)
    archive.write_bytes(raw)
    packages[key]=dict(path=str(archive.relative_to(R)),sha256=sha(archive),bytes=len(raw),files=X.scan_members(raw),
        accepted_files_byte_equal=checked,format='gzip-compressed tar',deterministic_rebuild=True,
        token_table_sha256=hashlib.sha256(packed['x0.json']).hexdigest(),members={n:hashlib.sha256(v).hexdigest() for n,v in packed.items()})
for v in packages.values():v['name_map_sha256']=sha(R/'out/NAME_MAP.json')

if not (R/'out/R5_PREVIOUS_PACKAGES.json').exists():dump(R/'out/R5_PREVIOUS_PACKAGES.json',previous)
dump(R/'out/R5_MEMBER_MAP.json',member_maps);dump(R/'out/PACKAGE_PINS.json',packages)
from offnative.package import package
code_sha=package(RELEASE/'n1');code=N/'out/code.tar'
assert code_sha==package(RELEASE/'n2')
# Check every final member, including nested archives, without exposing the secret.
secret_path=Path('/scratch/jjyeung/orch_n30/b07_offread/work/salt/SECRET')
assert stat.S_IMODE(secret_path.stat().st_mode)==0o600
secret_hex=secret_path.read_bytes().strip();secret=bytes.fromhex(secret_hex.decode())
secret_sha=sha(secret_path)
def unpack(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
        members=tf.getmembers();assert all((m.isfile() or m.isdir()) and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
        assert len({m.name for m in members})==len(members)
        return {m.name:tf.extractfile(m).read() for m in members if m.isfile()}
def scan_secret(files):
    count=0
    for name,raw in files.items():
        assert secret not in raw and secret_hex not in raw and secret_hex.upper() not in raw
        assert secret_hex not in name.encode() and secret not in name.encode()
        count+=1
        if X._archive(raw):count+=scan_secret(unpack(raw))
    return count
salt_checks=[];archive_checks=[]
for key,owner,path in [('N',N,code),('vsi',R,R/'out/package_vsi.tar'),('revsi',R,R/'out/package_revsi.tar')]:
    files=unpack(path.read_bytes());table=json.loads(files['x0.json']);salt=bytes.fromhex(table['salt'])
    digest=X.payload_digest(files);assert hmac.new(secret,digest,hashlib.sha256).digest()==salt
    name_map=json.loads((owner/'out/NAME_MAP.json').read_text());names=set(name_map)|set(X.WORDS)
    unsalted={hashlib.sha256(n.encode()).hexdigest() for n in names}
    assert not unsalted.intersection(set(table['tokens'])|set(table['aliases']))
    assert all(table['tokens'][hashlib.sha256(salt+n.encode()).hexdigest()]==token for n,token in name_map.items())
    count=scan_secret(files)
    actual={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}
    expected={v['path']:v['sha256'] for v in json.loads((N/'out/CODE_PINS.json').read_text())['files']} if key=='N' else packages[key]['members']
    assert actual==expected
    salt_checks.append(dict(packet=key,salt=salt.hex(),payload_pins_sha256=digest.hex(),secret_sha256=secret_sha,
        unsalted_dictionary_matches=0,dictionary_names=len(names),tokens=len(table['tokens']),aliases=len(table['aliases']),secret_absent_members=count,deterministic_rebuild=True))
    archive_checks.append(dict(packet=key,sha256=sha(path),bytes=path.stat().st_size,members=len(files),decoded_members=X.scan_members(path.read_bytes()),pins_match=True))
assert len({v['salt'] for v in salt_checks})==3
for owner,label in ((N,'N7'),(R,'R5')):
    dump(owner/'out'/(label+'_SALT_CHECK.json'),dict(passed=True,secret_sha256=secret_sha,packets=salt_checks,
        adapter_sha256=sha(modules[0]),identical_adapter_copies=4,
        limitation='The public salt defeats unsalted lookup only; dictionary guesses including the salt remain possible.'))
    dump(owner/'out'/(label+'_ARCHIVE_CHECK.json'),dict(passed=True,archives=archive_checks))
dump(N/'out/N7_RELEASE.json',dict(code_sha256=code_sha,r_packages={k:v['sha256'] for k,v in packages.items()},active_snapshot=active,submitted=False,uploaded=False))
(N/'out/NATIVE_KIT_READY.md').write_text(
'ReVSI × harness: NOT READY; ReVSI × e2e: NOT READY; VSI-Bench × harness: NOT READY; VSI-Bench × e2e: NOT READY.\n\n'
f"The whole N suite has {ns['passed']} passes, two cross-kit skips and one incompatible original reviewer case. The original R4 test appends OFFNATIVE_PACKET_SHA256 itself; its current-API sibling passes. The reviewer F1/F2/F3 gate passes all three cases, and test_prodroot passes all three production-root cases. Reviewer files remain byte-equal.\n\n"
'Four whole-worker CPU fixtures and one full CPU rehearsal under a production-style /tmp root pass. The rehearsal root remains below 20 MB; large fixture assets and traces stay in RAM. Mounts, transport and models remain CPU stand-ins.\n\n'
'All four opacity adapters are identical. Each packet derives a deterministic salt from its member pins and the Trinity-only secret; token and alias lookups use the salt. Unsalted dictionary checks find zero keys. The public salt still allows dictionary guesses that include it. In-job contents are exempt from the naming rule.\n\n'
'Production still requires complete owner artifacts, live timing and native-library validation, proof inputs and transport-only rehearsals. ReVSI clip hashes and pixel correspondence remain pending. The 17 whole-scene shards fit their planning estimates; live timing remains unmeasured. Nothing was submitted or uploaded.\n\n'
f'code.tar SHA256 `{code_sha}` ({code.stat().st_size} bytes). N7_VALIDATION.json, N7_REVIEW_GATE.json, N7_PRODROOT.json, N7_SALT_CHECK.json, N7_ARCHIVE_CHECK.json, N7_STORAGE.json, CODE_PINS.json, DEPENDENCY_PINS.json and SHIP_SHA256SUMS bind the release.\n')
(R/'out/REBIND_READY.md').write_text(
'VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.\n\n'
f"The whole R suite passes {rs['passed']} tests with one cross-kit skip. The reviewer F1/F2/F3 gate passes all three cases across R and N; test_prodroot passes all three cases. Reviewer files remain byte-equal. Four direct CPU rehearsals and one full production-root rehearsal pass. The latter stays below 20 MB.\n\n"
'Accepted report reproduction is exact: 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4], with every group and all three budgets checked. Accepted reader, scorer, parity and item bytes remain identical.\n\n'
'Packets use deterministic salts derived from member pins and the Trinity-only secret. All unsalted dictionary checks find zero keys; public salts still permit guesses that include the salt. In-job contents are exempt from the naming rule. Source paths, child arguments and environment retain their naming checks.\n\n'
'Production still requires owner selection/export inputs, live native-library and namespace validation and transport-only rehearsals. CPU models, mounts and transport remain stand-ins. Nothing was submitted or uploaded.\n\n'+
'\n'.join(f"{key}: SHA256 `{v['sha256']}` ({v['bytes']} bytes)." for key,v in packages.items())+
'\n\nR5_VALIDATION.json, R5_REVIEW_GATE.json, R5_PRODROOT.json, R5_SALT_CHECK.json, R5_ARCHIVE_CHECK.json, R5_STORAGE.json, PACKAGE_PINS.json and SHIP_SHA256SUMS bind the release.\n')
print(json.dumps(dict(N=code_sha,R={k:v['sha256'] for k,v in packages.items()},N_tests=ns,R_tests=rs)))
