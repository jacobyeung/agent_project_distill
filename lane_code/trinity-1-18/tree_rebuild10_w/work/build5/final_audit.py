"""Require final source, kit, package, suite and coverage identities to agree."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest,load
from launch_r2.build import verify,scan
def read(name):return json.loads((L/name).read_text())
seal=read('out/TREE_SEAL.json');delivery=read('work/build5/DELIVERY.json')
files=inventory(L/'work/tree_r1')
assert seal['files']==files and seal['tree_sha256']==digest(files)==delivery['source_revision']
for key,name in [('inventory_sha256','TREE_FILES.sha256'),('diff_sha256','TREE.diff')]:
    assert seal[key]==hashlib.sha256((L/'out'/name).read_bytes()).hexdigest()
archive=L/delivery['path']
assert archive.stat().st_size==delivery['bytes']<150_000_000
assert hashlib.sha256(archive.read_bytes()).hexdigest()==delivery['sha256']
fixture_counts=read('work/build5/proofs/fixtures/COUNTS.json')
assert all(value<=200 for value in fixture_counts['unique_examples_by_family'].values())
assert all(value<=200 for value in fixture_counts['total_examples_by_family'].values())
fixture_hashes={row['path']:row['sha256'] for row in fixture_counts['files']}
packaged={};harness={};checked_fixtures={};packaged_base={}
with tarfile.open(archive) as handle:
    names=set()
    for member in handle:
        assert member.isfile() and member.name not in names
        names.add(member.name)
        if member.name.startswith(('work/tree_r1/','work/base/tree_b01ce449/')) or member.name in fixture_hashes or member.name in {
            'work/build5/'+name for name in ('package.py','PACKAGE_TEST.sh','test_runner.py','compact_tmp.py','compare.py','coverage.py')}:
            h=hashlib.sha256()
            with handle.extractfile(member) as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
            if member.name.startswith('work/tree_r1/'):packaged[member.name[len('work/tree_r1/'):]]=h.hexdigest()
            elif member.name.startswith('work/base/tree_b01ce449/'):
                packaged_base[member.name[len('work/base/tree_b01ce449/'):]]=h.hexdigest()
            elif member.name in fixture_hashes:
                assert h.hexdigest()==fixture_hashes[member.name]
                checked_fixtures[member.name]=h.hexdigest()
            else:
                assert h.hexdigest()==hashlib.sha256((L/member.name).read_bytes()).hexdigest()
                harness[member.name]=h.hexdigest()
assert packaged==files
assert packaged_base==inventory(L/'work/base/tree_b01ce449')
assert checked_fixtures==fixture_hashes
kit_results=read('work/build5/kits/RESULTS.json')
tested={v['kit']:v for v in read('work/build5/proofs/package/KIT_TESTS.json')}
assert set(tested)=={'a0','a2'}
for value in kit_results:
    root=L/value['kit_path'];name=root.name
    assert verify(root)==value['kit_sha256']==tested[name]['sha256']
    assert scan(root)==dict(status='CLEAN',hits=0)==tested[name]['scan']
    assert load(root/'k/launch.json')['source_revision']==tested[name]['source_revision']=='sha256:'+seal['tree_sha256']
    assert not load(root/'k/launch.json')['production_authorized']
suite=read('work/build5/SUITE_COMPARISON.json')
for variant in ('tree','base'):assert read('work/build5/proofs/suite_'+variant+'/results.json')['complete']
assert not suite['fatal'] and suite['regressions']==0 and suite['r2_failures']==0 and suite['shared_grammar_failures']==0
coverage=read('work/build5/CHANGED_COVERAGE.json')
assert coverage['classes'].get('CPU-reachable unresolved',0)==0
for row in coverage['statements']:
    assert row['sha256']==hashlib.sha256((L/row['source']).read_bytes()).hexdigest()
    if not row['executed']:assert row.get('reason')
tested_archive=read('work/build5/proofs/package/ARCHIVE.json')
assert tested_archive['status']=='verified'
assert tested_archive['sha256']==delivery['sha256']
assert tested_archive['source_sha256']==seal['tree_sha256']
assert tested_archive['base_sha256']==digest(packaged_base)
assert tested_archive['fixtures_sha256']==digest(inventory(L/'fixtures'))
result=dict(status='CPU QUALIFIED; PRODUCTION CLOSED',source_revision=seal['tree_sha256'],
            package=delivery['path'],package_sha256=delivery['sha256'],harness=harness,
            suite_source='work/build5/SUITE_COMPARISON.json',coverage_source='work/build5/CHANGED_COVERAGE.json',
            real_frame_host_checked=False)
(L/'work/build5/FINAL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
