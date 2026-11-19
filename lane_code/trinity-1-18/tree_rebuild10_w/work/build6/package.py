"""Build and execute a portable snapshot from an otherwise empty directory."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
L=Path(__file__).resolve().parents[2]
out=L/'work/build6/proofs/package'
out.mkdir(parents=True,exist_ok=True)
archive=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else out/'input.tar'
members=[]
for relative in ('work/tree_r1','work/base/tree_b01ce449','fixtures','work/build6/kits','work/contracts_r6/tests_r6'):
    source=relative in ('work/tree_r1','work/base/tree_b01ce449')
    members.extend((p,str(p.relative_to(L))) for p in (L/relative).rglob('*') if p.is_file() and not p.is_symlink()
                   and not (source and set(p.relative_to(L/relative).parts)&{'.git','__pycache__','artifacts'}))
for name in ('test_runner.py','compact_tmp.py','package.py','PACKAGE_TEST.sh','compare.py','coverage.py'):
    members.append((L/'work/build6'/name,'work/build6/'+name))
size=sum(p.stat().st_size for p,_ in members)
subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
assert shutil.disk_usage('/scratch').free>=85*1024**3
assert size<150_000_000
if len(sys.argv)==1:
    with tarfile.open(archive,'w') as handle:
        for p,name in sorted(members,key=lambda x:x[1]):handle.add(p,arcname=name,recursive=False)
assert archive.stat().st_size<150_000_000
sys.path.insert(0,str(L/'work/build6'))
from compact_tmp import compact
prior_receipts=compact(L/'work/tmp',package_files=set())
(out/'PRIOR_TMP_RECEIPTS.json').write_text(json.dumps(prior_receipts,indent=2)+'\n')
root=Path(tempfile.mkdtemp(prefix='package6_',dir=L/'work/tmp'))
assert not any(root.iterdir())
with tarfile.open(archive) as handle:
    archive_members=handle.getmembers()
    unpacked_bytes=sum(member.size for member in archive_members if member.isfile())
    for member in archive_members:
        if member.issym() or member.islnk() or member.name.startswith('/') or '..' in Path(member.name).parts:
            raise ValueError('Unsafe package member')
    handle.extractall(root,filter='data')
    package_members=[member.name for member in archive_members if member.isfile()]
(root/'package_members.json').write_text(json.dumps(package_members))
kit_results=[]
sys.path.insert(0,str(root/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
source_before=inventory(root/'work/tree_r1')
base_before=inventory(root/'work/base/tree_b01ce449')
fixtures_before=inventory(root/'fixtures')
if (root/'work/build6/kits/a0').is_dir() and (root/'work/build6/kits/a2').is_dir():
    from launch_r2.build import verify,scan
    identity='sha256:'+digest(source_before)
    for name in ('a0','a2'):
        kit=root/'work/build6/kits'/name
        assert load(kit/'k/launch.json')['source_revision']==identity
        kit_results.append(dict(kit=name,sha256=verify(kit),scan=scan(kit),source_revision=identity))
elif len(sys.argv)>1:
    raise ValueError('Delivery package lacks both kits')
(out/'KIT_TESTS.json').write_text(json.dumps(kit_results,indent=2)+'\n')
if kit_results:
    # The delivered archive and standalone kits retain their bytes. Only these
    # verified temporary extraction copies become small hash receipts.
    sys.path.insert(0,str(root/'work/build6'))
    from compact_tmp import compact
    compacted=compact(root/'work/build6/kits')
    (out/'KIT_TMP_RECEIPTS.json').write_text(json.dumps(compacted,indent=2)+'\n')
env={**os.environ,'R2_LANE_ROOT':str(L),'R2_ALL_TESTS':'1','R2_PACKAGE_MEMBERS':str(root/'package_members.json')}
results={}
for variant,path in [('tree',root/'work/tree_r1'),('base',root/'work/base/tree_b01ce449')]:
    env['R2_TREE']=str(path)
    output=L/'work/build6/proofs'/('suite_'+variant)
    output.mkdir(exist_ok=True)
    combined=dict(tests=0,passed=[],failures=[],errors=[],skips=[],fatal=None,
                  completed_modules=0,scheduled_modules=0,complete=True,
                  coverage_code_filter='compiled-source fingerprint',groups=[])
    combined_hits={};source_hashes=None;sizes=[];module_inventory=[];codes={};returncodes=[]
    for group in ('generator','legacy','r2'):
        target=output/group;target.mkdir(exist_ok=True)
        for name in ('live_errors.json','live_failures.json'):
            (target/name).write_text('[]\n')
        (target/'progress.json').write_text(json.dumps(dict(completed=0,last=None,status='pending')))
    for group in ('generator','legacy','r2'):
        target=output/group;target.mkdir(exist_ok=True)
        env['R2_SUITE_GROUP']=group
        env['R2_BASE_RESULTS']=str(L/'work/build6/proofs/suite_tree'/group/'results.json')
        empty=Path(tempfile.mkdtemp(prefix='package_empty_',dir=str(L/'work/tmp')))
        assert not any(empty.iterdir())
        (output/'progress.json').write_text(json.dumps(dict(variant=variant,group=group,status='running',cwd=str(empty))))
        with (target/'console.log').open('w') as log:
            result=subprocess.run([sys.executable,'-I','-s','-B',str(root/'work/build6/test_runner.py'),str(target)],
                                  cwd=empty,env=env,stdout=log,stderr=subprocess.STDOUT)
        returncodes.append(result.returncode)
        if result.returncode<0:raise RuntimeError('Test process was killed; stop without retry')
        value=json.loads((target/'results.json').read_text())
        assert inventory(root/'fixtures')==fixtures_before,'Packaged fixtures changed during tests'
        for key in ('tests','completed_modules','scheduled_modules'):combined[key]+=value[key]
        for key in ('passed','failures','errors','skips'):combined[key].extend(value[key])
        combined['complete'] &= value['complete']
        if value['fatal']:combined['fatal']=(combined['fatal'] or '')+value['fatal']
        combined['tmp_bytes']=value['tmp_bytes']
        combined['groups'].append(dict(name=group,results=str(target/'results.json'),exit_code=result.returncode,cwd=str(empty)))
        hashes=json.loads((target/'source_hashes.json').read_text())
        if source_hashes is not None and source_hashes!=hashes:raise ValueError('Suite source changed between groups')
        source_hashes=hashes
        for name,lines in json.loads((target/'hits.json').read_text()).items():combined_hits.setdefault(name,set()).update(lines)
        sizes.extend(json.loads((target/'temporary_sizes.json').read_text()))
        module_inventory.extend(json.loads((target/'TEST_INVENTORY.json').read_text())['modules'])
        for name,count in json.loads((target/'rejected_code_objects.json').read_text()).items():codes[name]=codes.get(name,0)+count
        print(json.dumps(dict(variant=variant,group=group,tests=value['tests'],errors=len(value['errors']),failures=len(value['failures']))),flush=True)
    for name,value in [('results',combined),('hits',{k:sorted(v) for k,v in combined_hits.items()}),
                       ('source_hashes',source_hashes),('temporary_sizes',sizes),('rejected_code_objects',codes),
                       ('TEST_INVENTORY',dict(modules=module_inventory,discovered_tests=combined['tests']))]:
        (output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    results[variant]=dict(exit_code=int(any(returncodes)),source=str(path),result=str(output/'results.json'))
    (out/'RESULTS.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({variant:results[variant]}),flush=True)
assert inventory(root/'work/tree_r1')==source_before,'Packaged source changed during tests'
assert inventory(root/'work/base/tree_b01ce449')==base_before,'Packaged comparison base changed during tests'
(out/'ARCHIVE.json').write_text(json.dumps(dict(status='verified',
    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,unpacked_bytes=unpacked_bytes,
    source_sha256=digest(source_before),base_sha256=digest(base_before),fixtures_sha256=digest(fixtures_before)),indent=2))
