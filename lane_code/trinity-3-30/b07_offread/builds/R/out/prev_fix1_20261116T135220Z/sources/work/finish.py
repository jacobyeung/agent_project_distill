from pathlib import Path
import difflib
import hashlib
import io
import json
import re
import tarfile
import types
import dis

ROOT=Path.cwd()
OUT=ROOT/'out'
def sha(data):return hashlib.sha256(data).hexdigest()
def getfiles(root):return {str(p.relative_to(root)):p.read_bytes() for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()}
base={'vsi':getfiles(ROOT/'work/accepted_vsi')}
with tarfile.open(ROOT/'work/accepted_revsi.tar') as tf:
 base['revsi']={m.name:tf.extractfile(m).read() for m in tf if m.isfile()}
assert sha(Path('/scratch/jjyeung/orch_n30/b07_offread/in/x27/kit/package.tar').read_bytes())=='f42aa1a4aec049e03a321e88ccd8a5004a3e95963b08f18242db625bdec95684'
diffs=['# Changes against the accepted packages\n\nThe two tables cover every changed source line. The packet payloads, item inventories, step544 stager and scoring sources retain their accepted bytes. The new bootstrap checks authenticate the binding and require prompt parity before decoding. The D0 dispatcher stages media before the unchanged full checker needs its namespace bindings.\n\nPATH/ENV identifies only return-path substitutions and the Trinity package prefix. BEYOND identifies every other addition or removal. The complete line text appears in `out/SOURCE_vsi.patch` and `out/SOURCE_revsi.patch`; `out/SOURCE_DIFF.json` records the ranges and hashes. The new `RUN.md`, test files and this diff document are BEYOND in their entirety. This document excludes its own text from the patch to avoid self-reference.\n']
rows=[]
for key in ('vsi','revsi'):
 new=getfiles(ROOT/'kit'/key)
 diff=[]
 diffs.append('\n## '+('VSI-Bench' if key=='vsi' else 'ReVSI')+'\n\n| File | Accepted lines | Shipped lines | Class |\n|---|---:|---:|---|\n')
 diffs.append(f'| The Trinity package prefix moves to `kit/{key}/`. | All paths. | All paths. | PATH/ENV |\n')
 for name in sorted(set(base[key])|set(new)):
  a=base[key].get(name,b'');b=new.get(name,b'')
  if a==b:continue
  aa=a.decode().splitlines(True);bb=b.decode().splitlines(True)
  klass='PATH/ENV' if name=='launcher/orchard_results.py' else 'BEYOND'
  diff.extend(difflib.unified_diff(aa,bb,fromfile='accepted/'+name,tofile='kit/'+key+'/'+name,n=0))
  for op,i,j,k,l in difflib.SequenceMatcher(None,aa,bb,autojunk=False).get_opcodes():
   if op=='equal':continue
   ar=f'{i+1}–{j}' if j>i else 'None.';br=f'{k+1}–{l}' if l>k else 'None.'
   diffs.append(f'| `{name}` | {ar} | {br} | {klass} |\n')
   rows.append(dict(benchmark=key,path=name,old=[i+1,j],new=[k+1,l],classification=klass,old_sha256=sha(a),new_sha256=sha(b)))
 wrapper=(ROOT/'kit/rebind.py').read_text().splitlines(True)
 diffs.append(f'| `kit/rebind.py` is new on Trinity. | None. | 1–{len(wrapper)} | BEYOND |\n')
 diff.extend(difflib.unified_diff([],wrapper,fromfile='/dev/null',tofile='kit/rebind.py',n=0))
 for name in ['RUN.md']+[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tests').glob('*.py'))]:
  text=(ROOT/name).read_text().splitlines(True)
  diffs.append(f'| `{name}` is new on Trinity. | None. | 1–{len(text)} | BEYOND |\n')
  diff.extend(difflib.unified_diff([],text,fromfile='/dev/null',tofile=name,n=0))
 (OUT/f'SOURCE_{key}.patch').write_text(''.join(diff))
 diffs.append('\n')
(ROOT/'DIFF.md').write_text(''.join(diffs))
(OUT/'SOURCE_DIFF.json').write_text(json.dumps(rows,indent=1)+'\n')

# Enumerate inherited name strings without examining answers or choosing inputs.
terms=re.compile(r'(?i)(?:[A-Za-z0-9_.-]*(?:revsi|vsibench|scannet|arkit|qwen|legs1|rv_merge|distill|official|evalx|cp1m200|aws_vl64rt|cot)[A-Za-z0-9_.-]*)')
name_rows=[]
for key in ('vsi','revsi'):
 for name,raw in base[key].items():
  if not (name.startswith('launcher/') or name.startswith('reader/') or name.startswith('parity/') or name.startswith('cohort/')):continue
  if name.endswith(('.py','.sh')):
   hits=sorted(set(terms.findall(raw.decode())))
   if hits:name_rows.append(dict(benchmark=key,file=name,words=hits))
(OUT/'INHERITED_NAMES.json').write_text(json.dumps(name_rows,indent=1)+'\n')
words=sorted({w for r in name_rows for w in r['words']})
(OUT/'ORCHARD_NAMES.md').write_text('# Orchard name inventory\n\nThe accepted source packages already carry the strings below. `INHERITED_NAMES.json` identifies their source files. This inventory includes source literals; it does not claim that every literal becomes a live log line.\n\n'+', '.join('`'+w+'`' for w in words)+'.\n\nThe principal inherited names are `official5130`, `revsi`, `official999`, `COHORT_OFFICIAL6.jsonl`, `official_adapter.py`, `official_score.py`, `scannet`, `scannetpp`, `arkitscenes`, `Qwen3.5`, `qwen35`, `cp1m200`, `legs1_reads`, `rv_merge_fix`, `aws_vl64rt`, `evalx`, and `a15_cot_ap`. The new job identity uses only `a15_cot_ap` and a hexadecimal token. The new pool and GCS suffix use `9e6b70a213c84fd0`. Bootstrap fields `x0`, `x1`, `x2`, and `x3` carry hashes, a numeric variant and a byte count. BINDING.json and token meanings remain on Trinity.\n')

# Merge source-line evidence, retaining process boundaries and source hashes.
coverage=[]
for key in ('vsi','revsi'):
 work=ROOT/'work'/('coverage_'+key)
 result=json.loads((work/'RESULT.json').read_text())
 main=json.loads((OUT/('coverage_'+key+'_done.json')).read_text())
 pins=json.loads((OUT/('coverage_'+key+'_done_pins.json')).read_text())
 records={n:dict(sha256=pins.get(n),lines=v) for n,v in main.items()}
 child_paths=[Path(result['job_root'])/'exports/359fcc3c_m200/CHECK_LINES.json',Path(result['config']['spec']['run'])/'metadata/PARITY_LINES.json']
 for path in child_paths:
  for n,r in json.loads(path.read_text()).items():
   if n in records:records[n]['lines']=sorted(set(records[n]['lines'])|set(r['lines']))
   else:records[n]=r
 (OUT/('COVERAGE_'+key+'.json')).write_text(json.dumps(records,indent=1)+'\n')
 def executable(code):
  found={line for _,line in dis.findlinestarts(code) if line}
  for x in code.co_consts:
   if isinstance(x,types.CodeType):found |= executable(x)
  return found
 for name in ('launcher/orchard_job.py','launcher/orchard_stage.py','launcher/s1.py','launcher/export_stage.py','launcher/gate.py','launcher/orchard_results.py','launcher/orchard_launcher.py','launcher/return_io.py','launcher/trace_runtime.py','reader/chain.py','reader/official_adapter.py','reader/evaluator/worker.py'):
  p=ROOT/'kit'/key/name
  seen=set(records.get(str(p),{}).get('lines',[]))
  missing=sorted(executable(compile(p.read_bytes(),str(p),'exec'))-seen)
  coverage.append(dict(benchmark=key,file=name,executed=sorted(seen),unobserved=missing,sha256=sha(p.read_bytes())))
(OUT/'COVERAGE_LIMITS.json').write_text(json.dumps(coverage,indent=1)+'\n')
notes=['# Coverage limits\n\nThe D0 CPU rehearsals record executed lines in `COVERAGE_vsi.json` and `COVERAGE_revsi.json`, including the separate prompt-proof and full-checker subprocesses. `COVERAGE_LIMITS.json` lists all unobserved executable lines in the principal runtime files. Unobserved lines include error branches and unused step544 branches; they are not all Orchard-only.\n\nThe following operations require Orchard and were not executed: real runtime and model transfer, GCS credentials and object reads, the real namespace mount, real H100 admission, real processor loading, vLLM generation, GCS publication/readback, scheduler admission and submission, live governor registration, and network fetch. The mount, GPU and transport boundaries use local stand-ins. A fixed template stand-in passes the accepted prompt-byte proof, and the fake engine exercises the worker processor comparisons. Neither proves real-processor equivalence.\n\n| File | Unobserved executable lines |\n|---|---|\n']
for row in coverage:
 if row['file'].startswith('launcher/'):
  notes.append('| `kit/'+row['benchmark']+'/'+row['file']+'` | '+', '.join(map(str,row['unobserved']))+' |\n')
(OUT/'ORCHARD_ONLY.md').write_text(''.join(notes))

# Build flat regular-file archives; no inode reuse or tar hard-link entries are possible.
shipped={}
archives={}
common=['kit/rebind.py','RUN.md','DIFF.md']+[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tests').glob('*.py'))]
for key in ('vsi','revsi'):
 files={**{name:(ROOT/name).read_bytes() for name in common},**{'kit/'+key+'/'+n:v for n,v in getfiles(ROOT/'kit'/key).items()}}
 path=OUT/('package_'+key+'.tar')
 with tarfile.open(path,'w',format=tarfile.PAX_FORMAT) as tf:
  for name,raw in sorted(files.items()):
   m=tarfile.TarInfo(name);m.size=len(raw);m.mode=0o700 if name.endswith('.sh') else 0o644;m.mtime=0
   tf.addfile(m,io.BytesIO(raw));shipped[name]=sha(raw)
 with tarfile.open(path) as tf:
  assert all(m.isfile() and not m.islnk() and not m.issym() for m in tf)
 archives[key]=dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size,sha256=sha(path.read_bytes()),files=len(files))
 for name,raw in files.items():
  if name.endswith('.py'):compile(raw,name,'exec')
(OUT/'SHIP_SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(shipped.items())))
(OUT/'PACKAGE_PINS.json').write_text(json.dumps(archives,indent=1)+'\n')
(OUT/'OFFKIT_PINS.json').write_text(json.dumps({n:sha((Path('/scratch/jjyeung/orch_n30/b07_offread/kit/offkit')/n).read_bytes()) for n in ('bind.py','adapt_direct.py','report.py','spec.py')},indent=1)+'\n')
size=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file() and not p.is_symlink())
assert size<2_000_000_000,size
print(json.dumps(dict(archives=archives,workspace_bytes=size,shipped_files=len(shipped)),indent=2))
