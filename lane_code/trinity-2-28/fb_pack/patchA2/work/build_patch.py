"""Generate replacement and delta overlays and verify exact patch application."""
import difflib, hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'work/base'))
from student_pilot.source_seal import inventory
COMMAND='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/build_patch.py'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(name,obj):
    obj['command']=COMMAND
    obj.setdefault('inputs_sha256',{})[str(Path(__file__))]=sha(__file__)
    (ROOT/'out'/name).write_text(json.dumps(obj,indent=2)+'\n')
base,new,pa=(ROOT/'work'/n for n in ('base','new','patch_a'))
b,n,a=inventory(base),inventory(new),inventory(pa)
verification=json.loads((ROOT/'out/BASE_VERIFICATION.json').read_text())
assert b==verification['results']['base']['input_files_sha256']
def make(old, hashes, path):
    chunks=[]; files=[]
    for name in sorted(set(hashes)|set(n)):
        if hashes.get(name)==n.get(name):continue
        x=(old/name).read_text() if name in hashes else ''
        y=(new/name).read_text() if name in n else ''
        chunks.extend(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile='a/'+name if name in hashes else '/dev/null',tofile='b/'+name))
        files.append(dict(path=name,base_sha256=hashes.get(name),new_sha256=n.get(name)))
    path.write_text(''.join(chunks)); return files
full=ROOT/'out/PATCH_A2.patch'; delta=ROOT/'out/PATCH_A2_DELTA.patch'
files=make(base,b,full); changes=make(pa,a,delta)
inputs={str(ROOT/'out'/name):sha(ROOT/'out'/name) for name in ('BASE_VERIFICATION.json','LIVE_VERIFICATION.json','PATCH_A_INPUT.json','CAMERA_INPUT.json')}
for f in files:
    for tree,h in ((base,f['base_sha256']),(new,f['new_sha256'])):
        if h:inputs[str(tree/f['path'])]=h
put('FILES_TOUCHED.json',dict(status='OVERLAY_NOT_RESEALED',inputs_sha256=inputs,files=files,delta_files=changes,base_tree_sha256=verification['expected_tree_sha256'],patch_sha256=sha(full),delta_sha256=sha(delta)))
results=[]
for source,target,overlay in ((base,ROOT/'work/apply_base',full),(pa,ROOT/'work/apply_delta',delta),(ROOT/'work/live_base',ROOT/'work/live',full)):
    if not target.exists():shutil.copytree(source,target)
    command=['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-d',str(target)]
    p=subprocess.run(command,input=overlay.read_bytes(),capture_output=True)
    log=ROOT/'out'/('apply_'+target.name+'.log');log.write_bytes(p.stdout+p.stderr)
    assert p.returncode==0,(target,p.stdout,p.stderr)
    actual=inventory(target)
    expected=inventory(source)
    for f in files:expected[f['path']]=n[f['path']]
    assert actual==expected, target
    results.append(dict(tree=str(target),patch_command=command,returncode=p.returncode,files=len(actual),exact_application=True,log=str(log),log_sha256=sha(log)))
put('PATCH_VALIDATION.json',dict(status='PASS',inputs_sha256={**inputs,str(full):sha(full),str(delta):sha(delta)},results=results))
overlaps={}; other_inputs={}
ours={f['path'] for f in files}
for lane in ('camform','pointD','donor','prior2'):
    root=ROOT.parent/lane; manifest=root/'out/FILES_TOUCHED.json'
    if manifest.exists():
        raw=json.loads(manifest.read_text()); names={x['path'] for x in raw['files']}
        overlaps[lane]=dict(status='MANIFEST',overlap=sorted(ours&names),files=sorted(names),manifest=str(manifest))
        other_inputs[str(manifest)]=sha(manifest)
    else:
        code=root/'code'; paths=sorted(p for p in code.rglob('*') if p.is_file()) if code.exists() else []
        other_inputs.update({str(p):sha(p) for p in paths})
        # Report literal mentions, never infer an absent patch inventory.
        mentions={name for name in ours if any(name in p.read_text(errors='replace') for p in paths if p.suffix in ('.py','.sh','.md'))}
        overlaps[lane]=dict(status='MISSING_MANIFEST',expected=str(manifest),code_files=[str(p) for p in paths],literal_mentions=sorted(mentions),overlap='MISSING: final touched-file inventory')
cam=ROOT.parent/'camform/out/PATCH_CAMFORM.patch'
target=ROOT/'work/new_camform';shutil.copytree(new,target)
command=['patch','--batch','--fuzz=0','--no-backup-if-mismatch','-p1','-d',str(target)]
p=subprocess.run(command,input=cam.read_bytes(),capture_output=True)
(ROOT/'out/camform_apply.log').write_bytes(p.stdout+p.stderr)
other_inputs[str(cam)]=sha(cam)
put('OVERLAP.json',dict(inputs_sha256={**other_inputs,str(full):sha(full)},lanes=overlaps,camform=dict(status='PASS' if p.returncode==0 else 'FAIL',command=command,returncode=p.returncode,without_fuzz=p.returncode==0,log=p.stdout.decode()+p.stderr.decode())))
(ROOT/'STATUS.md').write_text(f'PATCH_A2 changes {len(files)} files against the sealed base; its delta changes {len(changes)} files against PATCH_A. Both patches reproduce the intended tree, and the replacement applies to the authenticated live tree without fuzz. Camform application and overlaps are recorded in out/OVERLAP.json. Regression suites are next.\n')
print(json.dumps(dict(changed=len(files),delta=len(changes),applications=results,overlaps=overlaps,camform_returncode=p.returncode)))
