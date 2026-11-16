from pathlib import Path
import json, hashlib
K=Path(__file__).resolve().parents[1]; P=K.parent/'pull'
orig={}
def copy(src,dst):
 s=P/src; d=K/dst; d.parent.mkdir(parents=True,exist_ok=True); d.write_bytes(s.read_bytes()); orig[str(d.relative_to(K))]=str(src)
base=Path('x27c/r2/sj/orch_cd/legs1_reads')
for n in ('common.py','export_check.py','direct.py'):copy(base/'out'/n,Path('reader/out')/n)
kit=Path('x27c/r2/sj/orch_cd/rv_merge_fix/work/r3/aws_vl64rt')
for s in (P/kit/'evaluator').rglob('*'):
 if s.is_file() and s.suffix in ('.py','.json'):copy(s.relative_to(P),Path('reader/evaluator')/s.relative_to(P/kit/'evaluator'))
for v in ('r3','r4','r5'):
 root=P/base/'work/vendor'/v
 names=['adapter.py']
 if v=='r3':names+=list(json.loads((root/'PINS.json').read_text()))+['PINS.json']
 if v=='r5':names+=['report.py','dev_scoring.py']
 for n in names:copy((root/n).relative_to(P),Path('reader/work/vendor')/v/n)
core=Path('x27/gs/f665/sj/orch_cd/evalx/work/milestone')
for n in ('orchard_launcher.py','orchard_stage.py','orchard_job.py','orchard_results.py','chain_save.py','stdout_transfer.py','ORCHARD_ASSETS.json'):copy(core/n,Path('launcher')/n)
copy(Path('x27/official/meta_5130.jsonl'),Path('cohort/meta_5130.jsonl'))
copy(Path('x27/res/e193/direct/main/PROMPT_PINS.json'),Path('parity/PROMPT_PINS.json'))
# Keep only the 20 prompt strings, never the large generation journals, in the proof payload.
r=[]
with (P/'x27/res/e193/direct/main/results/0/items_leg_m544_main.jsonl').open() as f:
 for line in f:
  if line.strip():
   row=json.loads(line); r.append({k:row[k] for k in ('example_id','prompt_text')})
  if len(r)==20:break
(K/'parity/ACCEPTED20.json').write_text(json.dumps(r,indent=2)+'\n')
heads=json.loads((P/'x27c/ebe/metadata/STAGING.json').read_text())['export_headers']
transport={k:heads[k] for k in ('archive_bytes','archive_sha256','members')}
transport.update(schema='transport-rebuilt-v1',step=544,artifact_sha256='1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef',parts=[{k:p[k] for k in ('name','generation','sha256','bytes','md5','offset')} for p in heads['parts']],provenance_sha256=hashlib.sha256((P/'x27c/ebe/metadata/STAGING.json').read_bytes()).hexdigest(),historical_attestation_recovered=False)
(K/'launcher/TRANSPORT.json').write_text(json.dumps(transport,indent=2)+'\n')
req=json.loads((P/'x27/res/e193/direct/main/request.json').read_text())
(K/'launcher/MODELS.json').write_text(json.dumps(req['models'],indent=2)+'\n')
paths={}
for alias in ('3e0e8a36','8b677689'):
 dataset=None
 for l in (P/f'x27/official/alias_{alias}_ls.txt').read_text().splitlines():
  if l.endswith('/:'):dataset=l[:-2]
  elif l.startswith('-') and l.endswith('.mp4'):
   name=dataset+'/'+l.split()[-1];paths.setdefault(name,[]).append('/project/community/jjyeung/'+alias+'/'+name)
sha=json.loads((P/'x27/official/VCHECK.json').read_text())['per_file_sha256']
assert len(sha)==288
manifest=[]
for name,h in sorted(sha.items()):
 assert len(paths[name])==1,(name,paths[name])
 manifest.append(dict(relative_path=name,alias_path=paths[name][0],sha256=h))
(K/'cohort/MEDIA_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
excluded={'object_abs_distance','room_size_estimation'}
rows=[json.loads(l) for l in (P/'x27/official/meta_5130.jsonl').read_text().splitlines()]
cohort=[]
for r in rows:
 if r['question_type'] in excluded:continue
 n=r['dataset']+'/'+r['scene_name']+'.mp4'
 cohort.append({k:r[k] for k in ('id','question_type','dataset','scene_name')}|dict(video_alias_path=paths[n][0],video_sha256=sha[n]))
assert len(cohort)==4008
(K/'cohort/COHORT_OFFICIAL6.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in cohort))
(K/'build/ORIGINS.json').write_text(json.dumps(orig,indent=2)+'\n')
print('Seeded',len(orig),'source files;',len(cohort),'items;',len(manifest),'videos')
