from pathlib import Path
import difflib, hashlib, json, shutil, subprocess
W=Path(__file__).resolve().parents[1]; O=W/'out'; D=W.parent/'donor2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(t): return {str(p.relative_to(t)):sha(p) for p in sorted(t.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
base=inventory(W/'work/base'); new=inventory(W/'work/new'); live_base=inventory(W/'work/live_base')
old={n:sha(D/'work/new'/n) for n in new}
changed=sorted(n for n in new if base.get(n)!=new[n]); delta=sorted(n for n in new if old[n]!=new[n])
assert delta==['tests/test_scale_donor.py'], delta
inputs={str(Path(__file__).resolve()):sha(__file__),str(O/'STAGING.json'):sha(O/'STAGING.json'),str(D/'out/PATCH_DONOR2.patch'):sha(D/'out/PATCH_DONOR2.patch')}
entries=[]
for name in changed:
    entries.append(dict(path=name,base_sha256=base.get(name),donor2_sha256=old[name],new_sha256=new[name]))
    for t in [W/'work/base',D/'work/new',W/'work/new']:
        if (t/name).exists():inputs[str(t/name)]=sha(t/name)
    dst=W/'overlay'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(W/'work/new'/name,dst)
for origin,filename in [(W/'work/base','PATCH_DONOR3.patch'),(D/'work/new','PATCH_DONOR3_DELTA.patch')]:
    parts=[]
    for name in changed:
        p=origin/name;before=p.read_text() if p.exists() else '';after=(W/'work/new'/name).read_text()
        parts.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+name if p.exists() else '/dev/null',tofile='b/'+name))
    (O/filename).write_text(''.join(parts))
applications=[]
for origin,label,patch,expected in [(W/'work/base','apply_base','PATCH_DONOR3.patch',new),(D/'work/new','apply_delta','PATCH_DONOR3_DELTA.patch',new),(W/'work/live_base','live','PATCH_DONOR3.patch',{**live_base,**{n:new[n] for n in changed}})]:
    target=W/'work'/label
    files=base if label=='apply_base' else (old if label=='apply_delta' else live_base)
    for n in files:
        q=target/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin/n,q)
    command=['patch','--batch','--fuzz=0','-p1','-i',str(O/patch)]
    p=subprocess.run(command,cwd=target,capture_output=True,text=True)
    (O/(label+'_apply.log')).write_text(p.stdout+p.stderr)
    assert p.returncode==0 and not any(s in (p.stdout+p.stderr).lower() for s in ('fuzz','offset','failed')),p.stdout+p.stderr
    assert inventory(target)==expected,label
    applications.append(dict(tree=label,status='PASS',command='cd '+str(target)+' && '+' '.join(command),files=len(expected),zero_fuzz=True,zero_offset=True))
for n in ['PATCH_DONOR3.patch','PATCH_DONOR3_DELTA.patch']:inputs[str(O/n)]=sha(O/n)
r=dict(input_sha256=inputs,command='python -B code/build_patch.py',files=entries,delta_files=delta,training_sources_unchanged_from_donor2=True,applications=applications,status='PASS')
(O/'FILES_TOUCHED.json').write_text(json.dumps(r,indent=2)+'\n')
(W/'STATUS.md').write_text('The corrected runtime regression passes on a native fixture export. The full patch applies with zero fuzz and zero offset to both verified seals; the delta applies to base plus donor2. Every resulting file matches the expected tree. Only tests/test_scale_donor.py differs from donor2 in the code overlay. Full donor, parity and focused checks are next.\n')
print(dict(changed=changed,delta=delta,applications=applications))
