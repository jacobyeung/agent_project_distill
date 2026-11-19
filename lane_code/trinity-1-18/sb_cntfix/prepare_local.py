from pathlib import Path
import ast, hashlib, json, shutil, tarfile
R=Path.cwd(); src=Path('/scratch/jjyeung/orch_n30/sb_cntrev')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,d,inputs):d['inputs_sha256']={str(x):sha(x) for x in inputs};Path(p).write_text(json.dumps(d,indent=2)+'\n')
(R/'k1').mkdir(exist_ok=True)
for n in ('labels_k1','teacher_k1_full'):shutil.copytree(str(src/'k1'/n),str(R/'k1'/n))
p=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w20/work/tree_r1/evalpath/official.py'); s=p.read_text(); lines=s.splitlines(True); tree=ast.parse(s)
func=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='official_mra'][0]
start=func.lineno-1; end=next(n.lineno-1 for n in tree.body if n.lineno>func.lineno)
code=''.join(lines[start:end]).rstrip()+'\n'
(R/'kit/files/official_vsi_mra.py').write_text('"""Pinned verbatim function from N evalpath/official.py; see MRA_SOURCE.json."""\nimport math\nfrom typing import Optional\n\n'+code)
pins=p.parent/'SOURCE_PINS.json';shutil.copy2(str(pins),str(R/'kit/files/MRA_UPSTREAM_PINS.json'))
dump(R/'kit/files/MRA_SOURCE.json',dict(source=str(p),function='official_mra',function_sha256=hashlib.sha256(code.encode()).hexdigest(),upstream=json.loads(pins.read_text())['score_and_aggregate.py']),[p,pins,R/'kit/files/official_vsi_mra.py'])
archive=Path('/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar')
wanted=['K1_PAIRS.json.gz','K1_LIFT.npz','K1_NMS.npz','K1_LMERGE.json','K1_LEARN_EST.json'];found=[]
with tarfile.open(str(archive)) as t:
 for m in t:
  if Path(m.name).name in wanted and m.isfile():
   dest=R/'kit/work'/Path(m.name).name
   with dest.open('wb') as f:shutil.copyfileobj(t.extractfile(m),f)
   found.append(m.name)
fixture=R/'kit/work/FIXTURE_MANIFEST.json';fm=json.loads(fixture.read_text());missing=[f['path'] for c in fm['captures'] for f in c['frames'] if not Path(f['path']).is_file()]
dump(R/'out/MISSING_INPUTS.json',dict(status='MISSING' if missing or len(found)<5 else 'COMPLETE',pilot_archive_matches=found,pilot_missing=[dict(name=n,expected_location=str(R/'kit/work'/n),searched_archive=str(archive)) for n in wanted if not (R/'kit/work'/n).exists()],fixture_missing=missing),[archive,fixture,R/'prepare_local.py'])
# The reviewed dev manifest is an authority copy, not a fresh scene mapping.
m=R/'review/MANIFEST_R0DEV.json';it=R/'kit/files/COUNT_ITEMS_535.jsonl'
dump(R/'kit/files/DEV_AUTHORIZATION.json',dict(schema='count-dev-allowlist-v1',evaluation_category='counting',set='R0-dev',items_sha256=sha(it),captures=json.loads(m.read_text())['captures']),[m,it])
for n in ('audit_cpu.py','audit_controls.py'):shutil.copy2(str(R/'review'/n),str(R/n))
