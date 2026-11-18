"""Refreeze a test-only fixture repair and authenticate unaffected suite shards."""
import ast,hashlib,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';O=L/'work/build12/proofs/n1/fixture_requalification'
O.mkdir(exist_ok=True);sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
old_root=L/'work/build12/proofs/n1/package/frozen';T=L/'work/tree_r1'
name='tests/test_carrier_c1_cp2.py';module='tests.test_carrier_c1_cp2'
before=inventory(old_root/'work/tree_r1');after=inventory(T)
changed=[n for n in set(before)|set(after) if before.get(n)!=after.get(n)]
assert changed==[name],changed
def without_method(raw):
    tree=ast.parse(raw)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ToolModeFlag')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_rows_apply_the_receipt_flag_to_routing_rows_only')
    method.body=[ast.Pass()]
    return ast.dump(tree,include_attributes=False)
assert without_method((old_root/'work/tree_r1'/name).read_text())==without_method((T/name).read_text())
assert not [str(p) for p in T.rglob('*.py') if p!=T/name and module.split('.')[-1] in p.read_text()]
for file in ('DELIVERY.json','KIT_RESULT.json','SUITE_COMPARISON.json'):
    (O/file).write_bytes((B/file).read_bytes())
for file in ('results.json','hits.json','source_hashes.json','temporary_sizes.json'):
    (O/('prior_'+file)).write_bytes((L/'work/build12/proofs/n1/suite_tree'/file).read_bytes())
prior=load(O/'prior_results.json');prior_hashes=load(O/'prior_source_hashes.json')
receipt=dict(changed_source_files=changed,unchanged_outside_test_method=True,
    no_other_module_imports_changed_test=True,prior_source=before,current_source=after,
    prior_archive=load(O/'DELIVERY.json'),method='Reuse unchanged test modules only; rerun the complete changed module from the new frozen archive. All production source, remaining tests, base, fixtures and runner bytes must match their original receipts.')
def run(label,command,**kwargs):
    (B/'STATUS.md').write_text('# Build 9fix status\n\nFinal fixture requalification: '+label+'. GO=false. Production source is unchanged. See proofs/fixture_requalification/RESUME_RECEIPT.json.\n')
    print(label,flush=True)
    result=subprocess.run(command,**kwargs)
    if result.returncode<0:raise RuntimeError('Process was killed; stop without retry')
    return result.returncode
py=[sys.executable,'-I','-s','-B']
assert run('seal',py+[str(B/'seal.py')])==0
(L/'work/build12/kits').rename(L/'work/build12/proofs/n1/kits/pre_fixture_source')
assert run('kits',py+[str(B/'stage9.py')])==0
assert run('packet',['bash',str(B/'PACKET_TEST.sh')])==0
assert run('delivery',py+[str(B/'make_delivery.py')])==0
(L/'work/build12/proofs/n1/package').rename(L/'work/build12/proofs/n1/package_initial')
P=L/'work/build12/proofs/n1/package';P.mkdir();root=P/'frozen';root.mkdir()
delivery=load(B/'DELIVERY.json');archive=L/delivery['path']
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
with tarfile.open(archive) as tar:
    members=tar.getmembers()
    assert not any(m.issym() or m.islnk() or m.name.startswith('/') or '..' in Path(m.name).parts for m in members)
    tar.extractall(root,filter='data')
    unpacked=sum(m.size for m in members if m.isfile())
    (root/'package_members.json').write_text(json.dumps([m.name for m in members if m.isfile()]))
assert inventory(root/'work/tree_r1')==after
old_archive=load(L/'work/build12/proofs/n1/package_initial/ARCHIVE.json')
assert digest(inventory(root/'work/base/tree_b01ce449'))==old_archive['base_sha256']
assert digest(inventory(root/'fixtures'))==old_archive['fixtures_sha256']
runner=root/'work/n1fix2/test_runner.py'
for group in ('generator','legacy','r2'):
    checkpoint=load(L/'work/build12/proofs/n1/suite_tree'/group/'GROUP_RECEIPT.json')
    assert checkpoint['complete']
    assert checkpoint['inputs']['source']==before
    assert checkpoint['inputs']['runner_sha256']==hashlib.sha256(runner.read_bytes()).hexdigest()
    assert checkpoint['inputs']['fixtures']==inventory(root/'fixtures')
    for key in ('bound_n1_inputs','bound_real_slices'):
        for path,sha in checkpoint['inputs'].get(key,{}).items():
            assert hashlib.sha256((L/path).read_bytes()).hexdigest()==sha
from launch_r1.build import verify as r1_verify
from launch_r2.build import verify as r2_verify
kits=[dict(kit=arm,sha256=(r1_verify if arm=='r1' else r2_verify)(root/'work/build12/kits'/arm),source_revision='sha256:'+digest(after)) for arm in ('r1','a0','a2')]
(P/'KIT_TESTS.json').write_text(json.dumps(kits,indent=2)+'\n')
target=L/'work/build12/proofs/n1/suite_tree/legacy_changed';target.mkdir(exist_ok=True)
empty=Path(tempfile.mkdtemp(prefix='fixture_final_',dir=L/'work/tmp'))
env={**os.environ,'R2_TREE':str(root/'work/tree_r1'),'R2_LANE_ROOT':str(L),
     'R2_PACKAGE_MEMBERS':str(root/'package_members.json'),'R2_ALL_TESTS':'1','R2_SUITE_GROUP':'legacy'}
with (target/'console.log').open('w') as log:
    code=run('frozen changed module',py+[str(runner),str(target),module],env=env,cwd=empty,stdout=log,stderr=subprocess.STDOUT)
current=load(target/'results.json');assert current['complete'] and current['fatal'] is None
test=module+'.ToolModeFlag.test_rows_apply_the_receipt_flag_to_routing_rows_only'
assert test in current['passed']
def selected(test):return test.startswith(module+'.')
old_count=sum(selected(r['test']) for r in load(O/'prior_temporary_sizes.json'))
assert old_count==current['tests'],(old_count,current['tests'])
combined=dict(prior)
for field in ('passed','failures','errors','skips'):
    combined[field]=[r for r in prior[field] if not selected(r if field=='passed' else r[0])]+current[field]
combined['tmp_bytes']=current['tmp_bytes']
combined['resume_receipt']='work/build12/proofs/n1/fixture_requalification/RESUME_RECEIPT.json'
combined['groups'].append(dict(name='legacy_changed',results=str(target/'results.json'),exit_code=code,cwd=str(empty)))
(L/'work/build12/proofs/n1/suite_tree/results.json').write_text(json.dumps(combined,indent=2)+'\n')
hits=load(O/'prior_hits.json');hashes=load(target/'source_hashes.json');fresh_hits=load(target/'hits.json')
for path in list(hits):
    if prior_hashes.get(path)!=hashes.get(path):hits[path]=fresh_hits.get(path,[])
for path,lines in fresh_hits.items():hits[path]=sorted(set(hits.get(path,[]))|set(lines))
(L/'work/build12/proofs/n1/suite_tree/hits.json').write_text(json.dumps(hits))
(L/'work/build12/proofs/n1/suite_tree/source_hashes.json').write_text(json.dumps(hashes))
receipt.update(status='PASS',rerun_module=module,rerun_tests=current['tests'],
    source_seal=digest(after),new_archive=delivery,
    retained_groups=['tree/generator','tree/r2','base/generator','base/legacy','base/r2'],
    retained_legacy_modules='All except '+module,
    prior_results_sha256=hashlib.sha256((O/'prior_results.json').read_bytes()).hexdigest(),
    changed_module_results_sha256=hashlib.sha256((target/'results.json').read_bytes()).hexdigest())
(O/'RESUME_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert inventory(root/'work/tree_r1')==after
(P/'ARCHIVE.json').write_text(json.dumps(dict(status='verified',sha256=delivery['sha256'],bytes=delivery['bytes'],
    unpacked_bytes=unpacked,source_sha256=digest(after),base_sha256=old_archive['base_sha256'],
    fixtures_sha256=old_archive['fixtures_sha256'],resume_receipt=combined['resume_receipt']),indent=2)+'\n')
(P/'RESULTS.json').write_text(json.dumps(dict(tree=str(L/'work/build12/proofs/n1/suite_tree/results.json'),base=str(L/'work/build12/proofs/n1/suite_base/results.json'),resume_receipt=combined['resume_receipt']),indent=2)+'\n')
print(json.dumps(dict(status='PASS',changed_module_tests=current['tests'],source_seal=digest(after))))
