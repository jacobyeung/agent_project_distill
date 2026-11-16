import ast, hashlib, json, pathlib, shutil, tarfile
B=pathlib.Path(__file__).resolve().parents[1]; BASE=B.parents[1]; W=BASE/'work/from113/work'; O=B/'out'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
src=BASE/'work/c8r_code'; dst=O/'guard_kit'
shutil.copytree(src,dst,dirs_exist_ok=True)
C=load(BASE/'work/from113/sub/b07a20b364/CONFIG.json');F=load(B/'in_c8r_kit/FAMILY.json')
dump(O/'BASELINE_CONFIG.json',C);dump(O/'BASELINE_FAMILY.json',F)
req=load(BASE/'work/ret544/native/paired/request.json');r1=load(BASE/'work/ret544/native/R1.json')
rows=r1['arms']['unflagged']; by={r['key']:r for r in rows}; assert req['keys']==r1['expected_keys']; assert set(by)==set(req['keys'])
dist=BASE/'guard_kit/report/inputs/DISTANCE_LIST_DEVS1_150.jsonl'
distance=[json.loads(s) for s in dist.read_text().splitlines()]
print('distance row',distance[0]);print('row fields',[(k,type(v).__name__) for k,v in rows[0].items()]);print('decode fields',rows[0]['decode'].keys())
print('unit',sorted({str(r.get('question_unit')) for r in rows if r['question_type']=='object_abs_distance'})[:10])
print('family keys',F.keys());print('limits',F['limits'])
print('small objects',[(x['role'],len(x['members']),x['bytes']) for x in F['assets']['small_objects']])
# Preserve exact accepted records and choose balanced coverage by order.
cam=['camera_displacement','camera_movement_direction','camera_rotation']; take=[]
for typ,n in zip(cam,[4,3,3]):take += [k for k in req['keys'] if by[k]['question_type']==typ][:n]
dr=[k for k in req['keys'] if by[k]['question_type']=='object_abs_distance']
units={k:by[k]['question_unit'] for k in dr};print('units example',list(units.items())[:4])
# Unit text parser from the report is pinned separately by the report.
import importlib.util
p=BASE/'guard_kit/report/inputs/unit_from_question.py';spec=importlib.util.spec_from_file_location('unit',p);u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
print('parser functions',[x for x in dir(u) if not x.startswith('_')])
print('task list keys',distance[0].keys())
with tarfile.open(W/'obj/metadata_e10fbb95487f3baf.tar') as t:
 members=[(x.name,x.size) for x in t if x.isfile()]
 dump(O/'METADATA_MEMBERS.json',members)
print('metadata members',members)
for name in ('export_stage.py','orchard_stage.py','orchard_job.py','chain_save.py','orchard_results.py','return_io.py'):
 target=dst/'reviewed'/name;target.parent.mkdir(exist_ok=True);shutil.copyfile(BASE/'work/from13/readk/kit/launcher'/name,target)
print('code bytes',sum(p.stat().st_size for p in dst.rglob('*') if p.is_file()))
with tarfile.open(BASE/'work/v1c/out/c.tar') as t:
 for n in ('proof.py','proof_stage.py','o.py','budget.py'):
  (B/'work'/('v1c_'+n)).write_bytes(t.extractfile(n).read())
