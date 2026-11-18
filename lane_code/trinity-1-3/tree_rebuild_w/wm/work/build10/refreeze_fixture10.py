"""Authenticate unchanged tests and rerun complete modules with corrected valid-call fixtures."""
import ast,hashlib,json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build10';O=L/'work/merge11/proofs/fixture_requalification'
O.mkdir(exist_ok=True);T=L/'work/tree_r1';sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
old_root=L/'work/merge11/proofs/package/frozen'
methods={
 'tests/test_batched_routed_decode.py':('BatchDecode','test_ragged_prompts_forced_responses_and_row_stops'),
 'tests/test_decode_parity_r9.py':('NativeFP32','test_torch_fallback_positions_and_no_recurrent_padding')}
modules=[name[:-3].replace('/','.') for name in methods]
before=inventory(old_root/'work/tree_r1');after=inventory(T)
changed=sorted(n for n in set(before)|set(after) if before.get(n)!=after.get(n))
assert changed==sorted(methods),changed
def outside_method(raw,clsname,methodname):
    parsed=ast.parse(raw);cls=next(n for n in parsed.body if isinstance(n,ast.ClassDef) and n.name==clsname)
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==methodname)
    method.body=[ast.Pass()]
    return ast.dump(parsed,include_attributes=False)
for name,(cls,method) in methods.items():
    assert outside_method((old_root/'work/tree_r1'/name).read_text(),cls,method)==outside_method((T/name).read_text(),cls,method)
references=[]
for p in T.rglob('*.py'):
    name=str(p.relative_to(T))
    if name in methods:continue
    text=p.read_text()
    for cls,_ in methods.values():
        if cls in text:references.append(dict(file=name,symbol=cls))
assert not references,references
if '--check-only' in sys.argv:
    print(json.dumps(dict(changed=changed,production_unchanged=True,test_method_bodies_only=True)))
    raise SystemExit(0)
for variant in ('tree','base'):
    result=load(L/'work/merge11/proofs'/('suite_'+variant)/'results.json')
    assert result['complete'] and result['fatal'] is None
for file in ('DELIVERY.json','KIT_RESULT.json','SUITE_COMPARISON.json'):
    (O/file).write_bytes((B/file).read_bytes())
for file in ('results.json','hits.json','source_hashes.json','temporary_sizes.json'):
    (O/('prior_'+file)).write_bytes((L/'work/merge11/proofs/suite_tree'/file).read_bytes())
prior=load(O/'prior_results.json');prior_hashes=load(O/'prior_source_hashes.json')
receipt=dict(changed_source_files=changed,unchanged_outside_test_methods=True,
    no_other_source_references_changed_classes=True,prior_source=before,current_source=after,
    prior_archive=load(O/'DELIVERY.json'),method='Reuse only unchanged test bodies, production source, base, fixtures, runner and bound inputs. Rerun both complete changed test modules from the final archive.')
def run(label,args,**kwargs):
    (B/'STATUS.md').write_text('# Build 10 status\n\nGO=false. Final test-fixture qualification: '+label+'. Production source is unchanged.\n')
    print(label,flush=True)
    result=subprocess.run(args,**kwargs)
    if result.returncode<0:raise RuntimeError('Process was killed; stop without retry')
    return result.returncode
py=[sys.executable,'-I','-s','-B']
assert run('seal',py+[str(B/'seal.py')])==0
retained=L/'work/merge11/proofs/kits/pre_fixture_source';assert not retained.exists();(B/'kits').rename(retained)
assert run('kits',py+[str(B/'stage9.py')])==0
assert run('packet',['bash',str(B/'PACKET_TEST.sh')])==0
assert run('delivery',py+[str(B/'make_delivery.py')])==0
retained=L/'work/merge11/proofs/package_initial';assert not retained.exists();(L/'work/merge11/proofs/package').rename(retained)
P=L/'work/merge11/proofs/package';P.mkdir();root=P/'frozen';root.mkdir()
delivery=load(B/'DELIVERY.json');archive=L/delivery['path']
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
with tarfile.open(archive) as tar:
    members=tar.getmembers()
    assert not any(m.issym() or m.islnk() or m.name.startswith('/') or '..' in Path(m.name).parts for m in members)
    tar.extractall(root,filter='data');unpacked=sum(m.size for m in members if m.isfile())
    (root/'package_members.json').write_text(json.dumps([m.name for m in members if m.isfile()]))
assert inventory(root/'work/tree_r1')==after
old_archive=load(retained/'ARCHIVE.json')
assert digest(inventory(root/'work/base/tree_b01ce449'))==old_archive['base_sha256']
assert digest(inventory(root/'fixtures'))==old_archive['fixtures_sha256']
runner=root/'work/build10/test_runner.py'
for group in ('generator','legacy','r2'):
    checkpoint=load(L/'work/merge11/proofs/suite_tree'/group/'GROUP_RECEIPT.json')
    assert checkpoint['complete'] and checkpoint['inputs']['source']==before
    assert checkpoint['inputs']['runner_sha256']==hashlib.sha256(runner.read_bytes()).hexdigest()
    assert checkpoint['inputs']['fixtures']==inventory(root/'fixtures')
    for key in ('bound_n1_inputs','bound_real_slices'):
        for path,sha in checkpoint['inputs'].get(key,{}).items():assert hashlib.sha256((L/path).read_bytes()).hexdigest()==sha
from launch_r1.build import verify as verify_r1
from launch_r2.build import verify as verify_r2
kits=[dict(kit=arm,sha256=(verify_r1 if arm=='r1' else verify_r2)(root/'work/build10/kits'/arm),source_revision='sha256:'+digest(after)) for arm in ('a2','a0','r1')]
(P/'KIT_TESTS.json').write_text(json.dumps(kits,indent=2)+'\n')
target=L/'work/merge11/proofs/suite_tree/legacy_changed';target.mkdir(exist_ok=True)
empty=Path(tempfile.mkdtemp(prefix='fixture_final_',dir=L/'work/tmp'))
env={**os.environ,'R2_TREE':str(root/'work/tree_r1'),'R2_LANE_ROOT':str(L),
    'R2_PACKAGE_MEMBERS':str(root/'package_members.json'),'R2_ALL_TESTS':'1','R2_SUITE_GROUP':'legacy'}
with (target/'console.log').open('w') as log:
    code=run('frozen changed test modules',py+[str(runner),str(target),*modules],env=env,cwd=empty,stdout=log,stderr=subprocess.STDOUT)
current=load(target/'results.json');assert current['complete'] and current['fatal'] is None
for name,(cls,method) in methods.items():assert name[:-3].replace('/','.')+'.'+cls+'.'+method in current['passed']
def selected(name):return any(name.startswith(module+'.') for module in modules)
old_count=sum(selected(r['test']) for r in load(O/'prior_temporary_sizes.json'))
assert old_count==current['tests'],(old_count,current['tests'])
combined=dict(prior)
for field in ('passed','failures','errors','skips'):
    combined[field]=[r for r in prior[field] if not selected(r if field=='passed' else r[0])]+current[field]
combined['tmp_bytes']=current['tmp_bytes'];combined['resume_receipt']='work/build10/proofs/fixture_requalification/RESUME_RECEIPT.json'
combined['groups'].append(dict(name='legacy_changed',results=str(target/'results.json'),exit_code=code,cwd=str(empty)))
(L/'work/merge11/proofs/suite_tree/results.json').write_text(json.dumps(combined,indent=2)+'\n')
hits=load(O/'prior_hits.json');hashes=load(target/'source_hashes.json');fresh=load(target/'hits.json')
for name in list(hits):
    if prior_hashes.get(name)!=hashes.get(name):hits[name]=fresh.get(name,[])
for name,lines in fresh.items():hits[name]=sorted(set(hits.get(name,[]))|set(lines))
(L/'work/merge11/proofs/suite_tree/hits.json').write_text(json.dumps(hits));(L/'work/merge11/proofs/suite_tree/source_hashes.json').write_text(json.dumps(hashes))
receipt.update(status='PASS',rerun_modules=modules,rerun_tests=current['tests'],source_seal=digest(after),new_archive=delivery,
    retained_groups=['tree/generator','tree/r2','base/generator','base/legacy','base/r2'],retained_legacy_modules='All except '+', '.join(modules),
    prior_results_sha256=hashlib.sha256((O/'prior_results.json').read_bytes()).hexdigest(),
    changed_module_results_sha256=hashlib.sha256((target/'results.json').read_bytes()).hexdigest())
(O/'RESUME_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert inventory(root/'work/tree_r1')==after
(P/'ARCHIVE.json').write_text(json.dumps(dict(status='verified',sha256=delivery['sha256'],bytes=delivery['bytes'],unpacked_bytes=unpacked,
    source_sha256=digest(after),base_sha256=old_archive['base_sha256'],fixtures_sha256=old_archive['fixtures_sha256'],resume_receipt=combined['resume_receipt']),indent=2)+'\n')
(P/'RESULTS.json').write_text(json.dumps(dict(tree=str(L/'work/merge11/proofs/suite_tree/results.json'),base=str(L/'work/merge11/proofs/suite_base/results.json'),resume_receipt=combined['resume_receipt']),indent=2)+'\n')
print(json.dumps(dict(status='PASS',changed_module_tests=current['tests'],source_seal=digest(after))))
