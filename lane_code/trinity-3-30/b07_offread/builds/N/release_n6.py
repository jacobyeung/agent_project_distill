"""Seal the validated N6/R4 sources and small evidence; build archives in RAM."""
from pathlib import Path
import gzip,hashlib,importlib.util,json,re,tarfile
N=Path(__file__).resolve().parent;R=N.parent/'R'
RAM=Path(json.loads((N/'out/N6_WORKSPACE.json').read_text())['ram'])
TMP=RAM/'release_final';TMP.mkdir(exist_ok=False)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(path,value):Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def suite(name,passed,failed=0):
    raw=(RAM/name).read_text()
    assert re.search(r'\b'+str(passed)+r' passed\b',raw),raw[-2000:]
    failures=re.findall(r'^FAILED (.+?) -',raw,re.M)
    if failed:assert failures==['kit/tests/test_review_offnative.py::test_R4_submit_argv_is_opaque'],failures
    else:assert not failures and ' failed' not in raw,raw[-2000:]
    return dict(passed=passed,failed=failed,summary=raw.strip().splitlines()[-1],log_sha256=sha(RAM/name))
ns=suite('n_final02.log',116,1);rs=suite('r_final02.log',40)
assert suite('proposal_final.log',1)['passed']==1
assert suite('review_r_final.log',2)['passed']==2
assert suite('review_n_final.log',1)['passed']==1
review=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative2/review_offnative2_tests')
review_pins={}
for name in ('test_review_offnative2.py','sim_r_namespace.py'):
    reference=(review/name).read_bytes()
    for d in (N/'kit/tests',R/'tests'):assert (d/name).read_bytes()==reference
    review_pins[name]=hashlib.sha256(reference).hexdigest()
original=review.parent.parent/'review_offnative/review_offnative_tests/test_review_offnative.py'
assert (N/'kit/tests/test_review_offnative.py').read_bytes()==original.read_bytes()
gate=dict(passed=3,failed=0,byte_equal=True,files=review_pins,cases=['F1','F2','F3'])
dump(N/'out/N6_REVIEW_GATE.json',gate);dump(R/'out/R4_REVIEW_GATE.json',gate)
for root,log,label in ((N,'n_final02.log','N6_TESTS.log'),(R,'r_final02.log','R4_TESTS.log')):
    (root/'out'/label).write_bytes((RAM/log).read_bytes())
for key in ('review_r_final','review_n_final','proposal_final','avunit01'):
    (N/'out'/('N6_'+key+'.log')).write_bytes((RAM/(key+'.log')).read_bytes())
fixtures=[]
for row in json.loads((RAM/'nf_end_index.json').read_text()):
    assert row['returncode']==0
    p=RAM/row['name']/'RESULT.json';value=json.loads(p.read_text());assert value['passed']
    fixtures.append(dict(row,path=str(p.parent),result_sha256=sha(p),trace_sha256=sha(RAM/(row['name']+'.json')),passed=True))
assert len(fixtures)==4
dump(N/'out/N6_FIXTURES.json',fixtures)
rehearsals=[]
for row in json.loads((RAM/'rf_end_index.json').read_text()):
    assert row['returncode']==0
    p=RAM/row['name']/'RESULT.json';value=json.loads(p.read_text());assert value['passed']
    rehearsals.append(dict(row,path=str(p.parent),result_sha256=sha(p),passed=True,items=value['items'],config_mode=value['config_mode'],boundaries=value['boundaries']))
assert len(rehearsals)==4
dump(R/'out/R4_REHEARSALS.json',rehearsals)
nonram=[]
for key,root in (('N',N/'work/nonshm_n04'),('R',N/'work/nonshm_r09')):
    p=root/('work/result/RESULT.json' if key=='N' else 'RESULT.json');value=json.loads(p.read_text());assert value['passed']
    if key=='N':
        check=json.loads((root/'work/NAMESPACE.json').read_text());assert check['passed'] and check['non_ram_branch']
    else:
        check=value['namespace_checks'];assert check and all(v['passed'] for v in check)
    size=sum(p.lstat().st_size for p in root.rglob('*') if p.is_file() or p.is_symlink())
    assert size<20_000_000,(key,size)
    nonram.append(dict(kit=key,path=str(root),passed=True,bytes=size,result_sha256=sha(p),namespace=check,
                       source_root_on_local_disk=True,large_fixture_assets_in_ram=True,live_mount_execution=False))
dump(N/'out/N6_NONSHM.json',nonram);dump(R/'out/R4_NONSHM.json',nonram[1])
validation=dict(suite=ns,reviewer=gate,original_reviewer=dict(passed=4,failed=1,byte_equal=True,sha256=sha(original),
    incompatible_case='R4 inserts OFFNATIVE_PACKET_SHA256 itself; current-API equivalent passes without weakened assertions'),
    supplemental_proposal_test=suite('proposal_final.log',1),supplemental_native_media_log_and_submission_tests=suite('avunit01.log',4),
    worker_fixtures=4,nonshm_rehearsals=1,shards=17,all_scene_costs_charged=True,
    readiness={b:{reader:'NOT READY' for reader in ('harness','e2e')} for b in ('revsi999t32','vsibench5130')})
dump(N/'out/N6_VALIDATION.json',validation)
dump(R/'out/R4_VALIDATION.json',dict(suite=rs,reviewer=gate,rehearsals=4,nonshm_rehearsals=1,
    exact_reproduction={'vsibench5130':{'score':68.77,'percentile_95':[66.5,71.0]},'revsi999t32':{'score':64.94,'percentile_95':[61.3,68.4]}},
    verification='Accepted-return tests assert exact equality for every group and all three budgets.',
    readiness={'vsibench5130':'NOT READY','revsi999t32':'NOT READY'}))
from offnative.io import tar_bytes
spec=importlib.util.spec_from_file_location('r_names',R/'kit/xnames.py');X=importlib.util.module_from_spec(spec);spec.loader.exec_module(X)
old_maps=json.loads((R/'out/R3_MEMBER_MAP.json').read_text());packages={};member_maps={};previous={}
for key in ('vsi','revsi'):
    archive=R/'out'/('package_'+key+'.tar')
    previous[key]=dict(sha256=sha(archive),bytes=archive.stat().st_size)
    names=set(old_maps[key].values())|{str(p.relative_to(R)) for p in (R/'tests').glob('*.py')}
    files={name:(R/name).read_bytes() for name in names if name not in ('xnames.py','0.py')}
    files['xnames.py']=(R/'kit/xnames.py').read_bytes()
    files['0.py']=b"import sys,xnames\nxnames.install('.')\nxnames.entry(['kit/rebind.py',*sys.argv[1:]])\n"
    with tarfile.open(archive) as tf:
        checked=0
        for physical,logical in old_maps[key].items():
            if any(part in logical for part in ('/reader/','/cohort/','/inputs/','/parity/')):
                assert tf.extractfile(physical).read()==files[logical],logical
                checked+=1
    member_maps[key]={X.path_name(name):name for name in files}
    packed,changed=X.pack(files);assert not changed
    raw=gzip.compress(tar_bytes(packed),mtime=0);count=X.scan_members(raw)
    staged=TMP/(key+'.tar');staged.write_bytes(raw)
    # Previous archive identities are retained; another archive copy exceeds the storage allowance.
    archive.write_bytes(staged.read_bytes())
    packages[key]=dict(path=str(archive.relative_to(R)),bytes=len(raw),sha256=sha(archive),files=count,
        format='gzip-compressed tar',accepted_files_byte_equal=checked,
        token_table_sha256=hashlib.sha256(packed['x0.json']).hexdigest(),members={n:hashlib.sha256(v).hexdigest() for n,v in packed.items()})
    with tarfile.open(archive) as tf:
        assert {m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf}==packages[key]['members']
for value in packages.values():value['name_map_sha256']=sha(R/'out/NAME_MAP.json')
dump(R/'out/R4_PREVIOUS_PACKAGES.json',previous)
dump(R/'out/R4_MEMBER_MAP.json',member_maps);dump(R/'out/PACKAGE_PINS.json',packages)
dump(R/'out/R4_ARCHIVE_CHECK.json',dict(passed=True,packages=packages))
from offnative.package import package
code_sha=package(TMP/'n');code=N/'out/code.tar';pins=json.loads((N/'out/CODE_PINS.json').read_text())
from offnative.opacity import scan_members
with tarfile.open(code) as tf:actual={m.name:hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf}
assert actual=={r['path']:r['sha256'] for r in pins['files']}
assert scan_members(code.read_bytes())>=len(actual)
dump(N/'out/N6_ARCHIVE_CHECK.json',dict(passed=True,sha256=code_sha,bytes=code.stat().st_size,members=len(actual),name_map_sha256=sha(N/'out/NAME_MAP.json')))
dump(N/'out/N6_RELEASE.json',dict(code_sha256=code_sha,r_packages={k:v['sha256'] for k,v in packages.items()},active_snapshot=json.loads((N/'vendor/ACTIVE.json').read_text()),submitted=False,uploaded=False))
(N/'out/NATIVE_KIT_READY.md').write_text(
    'ReVSI × harness: NOT READY; ReVSI × e2e: NOT READY; VSI-Bench × harness: NOT READY; VSI-Bench × e2e: NOT READY.\n\n'
    'The whole N suite has 116 passes, two cross-kit skips and one incompatible original reviewer case. The byte-equal new reviewer gate passes all three findings across N and R. The original R4 case fails because it inserts the retired OFFNATIVE_PACKET_SHA256 export itself; its current-API sibling preserves the naming assertion and checks the exact export, account and no-requeue flags. The other four original reviewer cases pass.\n\n'
    'Four whole-worker CPU fixtures and the full non-RAM worker rehearsal pass. Native video paths resolve to SHA-keyed files; child argv scans cover bwrap and subprocesses. Child diagnostics stay in the job logs without per-call descriptor leaks. Proposal-root injection exists only in tests.\n\n'
    'The 17 whole-scene shards charge every scene once and include staging, G3T, SAM, primary loading, proof assets and decodes, the second proof model load, canary work and reserve. The maximum estimate is 21,450.845 seconds including 600 seconds reserved for return. Timing allowances remain unmeasured and do not certify completion.\n\n'
    'Production still needs complete owner artifacts, live timing and native-library validation, the relevant proof inputs and transport-only rehearsals. ReVSI clip hashes and pixel correspondence remain pending. The orchestrator must rule on naming exemptions for unchanged source contents and digest tables. Nothing was submitted or uploaded.\n\n'
    f'code.tar SHA256 `{code_sha}` ({code.stat().st_size} bytes). N6_VALIDATION.json, N6_NONSHM.json, N6_REVIEW_GATE.json, CODE_PINS.json, DEPENDENCY_PINS.json and SHIP_SHA256SUMS bind this release.\n')
(R/'out/REBIND_READY.md').write_text(
    'VSI-Bench × direct: NOT READY for production; ReVSI × direct: NOT READY for production.\n\n'
    'The whole R suite passes 40 tests with one cross-kit skip. The byte-equal F1 and F2 tests pass, as does N\'s byte-equal F3 test. Four CPU direct rehearsals and one full non-RAM rehearsal pass. Accepted report reproduction is exact: 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4], with every group and all three budgets checked.\n\n'
    'The shell interpreter agrees with its opaque namespace bind. Media binds and native decoder lookup use SHA-keyed files; every child argv is scanned. Native diagnostics remain in the job logs. Accepted reader, scorer, parity and item bytes remain identical.\n\n'
    'Production still requires owner selection/export inputs, live native-library and namespace validation, a transport-only rehearsal and an orchestrator ruling on source-content naming exemptions. CPU models, mounts and transport are stand-ins. Nothing was submitted or uploaded.\n\n'+
    '\n'.join(f"{key}: SHA256 `{v['sha256']}` ({v['bytes']} bytes)." for key,v in packages.items())+
    '\n\nR4_VALIDATION.json, R4_NONSHM.json, R4_ARCHIVE_CHECK.json, PACKAGE_PINS.json and SHIP_SHA256SUMS bind this release.\n')
print(json.dumps({'N':code_sha,'R':{k:v['sha256'] for k,v in packages.items()}},sort_keys=True))
