from pathlib import Path
import ast,base64,hashlib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1'
sys.path[:0]=[str(L/'work/build24'),str(L/'work/tree_r1')]
import joblib as J
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
base=J.load(D/'BASELINE.json');actual=inventory(L/'work/tree_r1')
assert actual==base['tree']['files'];tree=digest(actual)
assert tree=='189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710'
for name,v in base['packages'].items():assert J.sha(L/'out'/name)==v['sha256']
changed={};seals={};protected=('k/c.json','k/n.json','k/c0.json','k/7.json','k/h.json','k/r.json','k/p.json','b/z.py','b/resolve.py')
for name in ('q','n','n_go'):
 k=L/('out/kit_n_go' if name=='n_go' else 'work/build24/kits/'+name);seal=verify(k);seals[name]=seal
 assert J.load(D/('SCAN_'+name+'.json'))['kit_seal']==seal
 for rel in protected:assert J.sha(k/rel)==base['kits'][name][rel]['sha256'],(name,rel)
 assert J.load(k/'k/a.json')['GO']==(name=='n_go')
 changed[name]=[str(p.relative_to(k)) for p in k.rglob('*') if p.is_file() and (str(p.relative_to(k)) not in base['kits'][name] or J.sha(p)!=base['kits'][name][str(p.relative_to(k))]['sha256'] or p.stat().st_mode&511!=base['kits'][name][str(p.relative_to(k))]['mode'])]
 for p in k.glob('b/*.py'):ast.parse(p.read_text())
 assert all(p.stat().st_mode&511==0o755 for p in [k/'job.sh',*k.glob('b/*.sh')])
 for p in k.rglob('*.pyc'):raise AssertionError(p)
uploads=J.load(L/'out/UPLOADS_24M1.json')
for v in uploads['files']:
 p=Path(v['local_path']);assert J.sha(p)==v['sha256'] and p.stat().st_size==v['bytes'] and format(p.stat().st_mode&511,'04o')==v['mode']
for v in J.load(L/'work/build24k/UPLOADS_n.json')['files']:
 if v['opaque_name'].startswith('u/'):assert J.sha(v['local_path'])==v['sha256']
for f in ('MODE_R_TEST','FRAME_TESTS','FAILURE_TESTS','P_REFRESH_TESTS','Q_SELECTION_TEST','ROUTING_TESTS','RETAINED_EVIDENCE','STATIC_TESTS'):
 assert J.load(D/(f+'.json'))['status']=='PASS',f
assert all(x['returncode']==0 for x in J.load(D/'SUITES.json'))
assert all(x['status']=='BOUNDARY' for x in J.load(D/'SEQUENCE.json').values())
assert J.load(D/'KIT_TESTS.json')['successful'] and J.load(D/'NAMING_TESTS.json')['successful']
J.write(D/'INVARIANTS.json',dict(status='PASS',tree_sha256=tree,tree_files=len(actual),kits=seals,protected_kit_files_unchanged=list(protected),changed=changed,packages_unchanged=len(base['packages']),retained_uploaded_inputs_restored_and_verified=True,GO_upload=False))
J.write(D/'VALIDATION.json',dict(status='PASS',suites=J.load(D/'SUITES.json'),mode_r=J.load(D/'MODE_R_TEST.json'),hidden_path=J.load(D/'SEQUENCE.json'),operational_exception='The test-only transport exceeded the 200 MB transient disk cap; retained inputs were restored and generated copies replaced by references. This is not a fully constraint-compliant run.'))
print('tree, packages, protected fields, upload closure and tests PASS')
