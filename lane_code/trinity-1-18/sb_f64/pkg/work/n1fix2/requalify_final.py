"""Qualify the final host module while retaining source-bound unaffected groups."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
initial=L/'work/build12/proofs/n1/package/frozen'
before=inventory(initial/'work/tree_r1');after=inventory(T)
changed={k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
assert changed=={'launch_r1/build.py','launch_r1/entry.py','tests/test_r2_n1fix.py'},changed
retained=[]
for group in ('generator','legacy'):
    folder=L/'work/build12/proofs/n1/suite_tree'/group
    receipt=json.loads((folder/'GROUP_RECEIPT.json').read_text())
    assert receipt['complete'] and receipt['inputs']['source']==before
    assert receipt['inputs']['fixtures']==inventory(L/'fixtures')
    assert receipt['inputs']['runner_sha256']==hashlib.sha256((B/'test_runner.py').read_bytes()).hexdigest()
    observed=json.loads((folder/'hits.json').read_text())
    assert not changed.intersection(k for k,v in observed.items() if v)
    # The only modified test module belongs to r2. No retained module imports
    # the host entry; the retained groups execute no statements from it.
    testpaths=(initial/'work/tree_r1/tests').glob('test_*.py') if group=='legacy' else (initial/'work/tree_r1/generator').rglob('test_*.py')
    for p in testpaths:
        if p.name.startswith('test_r2'):continue
        assert 'launch_r1' not in p.read_text(),str(p)
    retained.append(dict(group=group,receipt=str(folder/'GROUP_RECEIPT.json'),
        receipt_sha256=hashlib.sha256((folder/'GROUP_RECEIPT.json').read_bytes()).hexdigest(),
        unchanged_inputs='All executed source modules, test modules, fixtures and runner bytes match; the host entry is neither imported directly by these tests nor executed.'))
proof=L/'work/build12/proofs/n1/final_requalification';proof.mkdir(exist_ok=True)
(proof/'RESUME_RECEIPT.json').write_text(json.dumps(dict(changed_files=sorted(changed),before=before,after=after,retained=retained),indent=2)+'\n')
def run(name,args):
    (B/'STATUS.md').write_text('# Build n1fix status\n\nFinal qualification: '+name+'. GO=false. Unaffected generator and legacy groups have bound resume receipts in proofs/final_requalification.\n')
    with (B/('final_'+name+'.log')).open('w') as log:
        code=subprocess.run(args,cwd=L,stdout=log,stderr=subprocess.STDOUT).returncode
    print(name,code,flush=True)
    if code<0:raise SystemExit('A process was killed; stop without retry.')
    if code:raise SystemExit(code)
py=[sys.executable,'-I','-s','-B']
run('seal',py+[str(B/'seal.py')])
run('packet',['bash',str(B/'PACKET_TEST.sh')])
(L/'work/build12/kits').rename(L/'work/build12/proofs/n1/kits/pre_host_token')
run('kits',py+[str(B/'stage9.py')])
run('delivery',py+[str(B/'make_delivery.py')])
delivery=json.loads((B/'DELIVERY.json').read_text());archive=L/delivery['path']
out=L/'work/build12/proofs/n1/package_final';out.mkdir(exist_ok=True);root=out/'frozen';root.mkdir(exist_ok=True)
assert not any(root.iterdir())
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
with tarfile.open(archive) as handle:
    members=handle.getmembers()
    assert all(not m.issym() and not m.islnk() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)
    handle.extractall(root,filter='data')
    unpacked=sum(m.size for m in members if m.isfile())
(root/'package_members.json').write_text(json.dumps([m.name for m in members if m.isfile()]))
assert inventory(root/'work/tree_r1')==after
assert inventory(root/'fixtures')==inventory(L/'fixtures')
assert inventory(root/'work/base/tree_b01ce449')==inventory(L/'work/base/tree_b01ce449')
target=L/'work/build12/proofs/n1/suite_tree/r2_final';target.mkdir(exist_ok=True)
env={**os.environ,'R2_TREE':str(root/'work/tree_r1'),'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'1',
     'R2_SUITE_GROUP':'r2','R2_PACKAGE_MEMBERS':str(root/'package_members.json')}
empty=L/'work/tmp/final_suite_empty';empty.mkdir(exist_ok=True);assert not any(empty.iterdir())
with (target/'console.log').open('w') as log:
    code=subprocess.run(py+[str(root/'work/n1fix2/test_runner.py'),str(target)],cwd=empty,env=env,
                        stdout=log,stderr=subprocess.STDOUT).returncode
if code<0:raise SystemExit('Final r2 suite killed; stop without retry.')
value=json.loads((target/'results.json').read_text())
(target/'GROUP_RECEIPT.json').write_text(json.dumps(dict(inputs=dict(source=after,fixtures=inventory(L/'fixtures'),
    runner_sha256=hashlib.sha256((B/'test_runner.py').read_bytes()).hexdigest()),complete=value['complete'],returncode=code,cwd=str(empty)),indent=2))
combined=dict(tests=0,passed=[],failures=[],errors=[],skips=[],fatal=None,completed_modules=0,scheduled_modules=0,
              complete=True,coverage_code_filter='compiled-source fingerprint',groups=[])
hits={};hashes={}
for group in ('generator','legacy','r2_final'):
    folder=L/'work/build12/proofs/n1/suite_tree'/group;v=json.loads((folder/'results.json').read_text())
    for key in ('tests','completed_modules','scheduled_modules'):combined[key]+=v[key]
    for key in ('passed','failures','errors','skips'):combined[key].extend(v[key])
    combined['complete'] &= v['complete'];combined['fatal']=combined['fatal'] or v.get('fatal')
    combined['groups'].append(dict(name=group,result=str(folder/'results.json'),retained=group!='r2_final'))
    source=json.loads((folder/'source_hashes.json').read_text())
    for name,lines in json.loads((folder/'hits.json').read_text()).items():
        if source.get(name)==after.get(name):
            hits.setdefault(name,set()).update(lines);hashes[name]=source[name]
folder=L/'work/build12/proofs/n1/suite_tree'
for name,v in [('results',combined),('hits',{k:sorted(v) for k,v in hits.items()}),('source_hashes',hashes)]:
    (folder/(name+'.json')).write_text(json.dumps(v,indent=2)+'\n')
from launch_r1.build import verify as verify1
from launch_r2.build import verify as verify2
kits=[dict(kit=name,sha256=(verify1 if name=='r1' else verify2)(root/'work/build12/kits'/name)) for name in ('a0','a2','r1')]
receipt=dict(status='verified',sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,
             unpacked_bytes=unpacked,source_sha256=digest(after),base_sha256=digest(inventory(root/'work/base/tree_b01ce449')),
             fixtures_sha256=digest(inventory(root/'fixtures')),requalification=str(proof/'RESUME_RECEIPT.json'))
for where in (out,L/'work/build12/proofs/n1/package'):
    (where/'ARCHIVE.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (where/'KIT_TESTS.json').write_text(json.dumps(kits,indent=2)+'\n')
assert inventory(root/'work/tree_r1')==after
print(json.dumps(dict(tests=combined['tests'],r2_tests=value['tests'],r2_failures=len(value['failures']),r2_errors=len(value['errors']))))
