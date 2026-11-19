"""Run the real routing mode in the read-only project view; reuse retained inputs."""
from pathlib import Path
import sys, os, json, base64, hashlib, shutil, subprocess, shlex, time, signal
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1';F=D/'mode_r_v9';F.mkdir();node=F/'node';node.mkdir();(node/'tmp').mkdir()
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build24f'),str(L/'work/tree_r1')]
import joblib as J
from kit24f import reseal
kit=F/'kit'
def kitcopy(a,b):
    if Path(a).name in ('p.json','r.json','BUILD.json','SHA256SUMS.txt'):return shutil.copyfile(a,b)
    os.link(a,b);return b
shutil.copytree(L/'work/build24/kits/n',kit,copy_function=kitcopy)
def cap(p,v):
    doc=json.loads(p.read_text());raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
    doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest());p.write_text(json.dumps(doc))
project=F/'project';target=project/'n';(target/'u').mkdir(parents=True);(target/'o/94/live').mkdir(parents=True)
spec=J.load(kit/'k/p.json');spec.update(step=600,uploads=[],host_paths={},n_root='/project/n')
for item in J.load(L/'work/build24k/UPLOADS_n.json')['files']:
    if item['opaque_name'].startswith('u/'):
        (target/'u'/item['sha256']).symlink_to(item['local_path'])
        spec['uploads'].append(dict(sha256=item['sha256'],bytes=item['bytes']))
cap(kit/'k/p.json',spec)
resolved=J.load(L/'work/build24k/mode_r_test_v5/request.json')['_resolved']
base=J.load(kit/'k/r.json');base['routing_base']=resolved['config']['streams']['routing'];cap(kit/'k/r.json',base)
resolved['kit_sha256']=reseal(kit);J.write(node/'r.json',dict(_resolved=resolved))
# Reuse retained payload inodes through the same bind mount as the job output.
reuse=node/'reuse';reuse.mkdir();inode_paths={}
sources=[p for p in (L/'work/build24/proofs/capacity').rglob('*') if p.is_file()]
sources += [p for p in kit.rglob('*') if p.is_file()]
sources += [Path(x['local_path']) for x in J.load(L/'work/build24k/UPLOADS_n.json')['files'] if x['opaque_name'].startswith('u/')]
for source in sources:
    source=source.resolve();st=source.stat()
    if st.st_size<=100000:continue
    key=str(st.st_ino)
    if key not in inode_paths:
        os.link(source,reuse/key);inode_paths[key]='/tmp/q_22c714e1/reuse/'+key
J.write(node/'reuse.json',inode_paths)
# Retained fixture bytes are hardlinked by the authenticated staging copier.
# This transport substitution saves disk; hashes and native staging checks run.
boundary=F/'boundary.py'
boundary.write_text('''from pathlib import Path
import sys,runpy,os,shutil
L=Path('''+repr(str(L))+''')
sys.path[:0]=[str(L/'work/build24'),str(L/'work/build21'),str(L/'work/tree_r1'),str(Path(sys.argv[1]).parent)]
import native24 as N
N.C.processor_for=N.processor
import pl,rg,z
import io
original_open=Path.open
class VerifiedSink(io.BytesIO):
 def __init__(self,path):super().__init__();self.path=path
 def close(self):
  if not self.closed:
   assert __import__('hashlib').sha256(self.getvalue()).hexdigest()==z.sha(self.path)
  super().close()
def isolated_open(path,mode='r',*args,**kwargs):
 if mode=='wb' and str(path).startswith('/tmp/q_22c714e1/p/q/u/') and path.exists() and path.stat().st_nlink>1:
  return VerifiedSink(path)
 return original_open(path,mode,*args,**kwargs)
Path.open=isolated_open
copy=shutil.copyfile
inode_map=__import__('json').loads(Path('/tmp/q_22c714e1/reuse.json').read_text())
def reuse(a,b,*args,**kwargs):
 a,b=Path(a),Path(b)
 if not b.exists() and a.is_file() and a.stat().st_size>100000:
  os.link(inode_map.get(str(a.stat().st_ino),str(a)),b);return str(b)
 return copy(a,b,*args,**kwargs)
shutil.copyfile=reuse
original_plan=pl.plan_payload
def planned(*args,**kwargs):
 req,paths,stage=original_plan(*args,**kwargs)
 def wrapped(entries,directory):
  # Pre-bind large authenticated inputs to their retained bytes, without copies.
  plan=z.load(Path(directory).parent/'plan.json')
  stage_vars=dict(zip(stage.__code__.co_freevars,[c.cell_contents for c in stage.__closure__]))
  for name,e in entries.items():
   if 'sha256' not in e or e.get('bytes',0)<=100000:continue
   h=e['sha256'];source=stage_vars['copies'].get(name) or paths.get(h)
   if source and Path(source).is_file():
    dst=Path(directory)/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():os.link(inode_map.get(str(Path(source).stat().st_ino),source),dst)
  return stage(entries,directory)
 wrapped.close=stage.close
 return req,paths,wrapped
pl.plan_payload=planned
native=rg.regenerate
rg.regenerate=lambda cfg,root:native(cfg,root,compare=False)
helper=sys.argv[1];sys.argv=sys.argv[1:]
runpy.run_path(helper,run_name='__main__')
''')
outer=['/usr/bin/bwrap','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc','--ro-bind','/scratch','/scratch','--tmpfs','/tmp','--dev-bind','/dev','/dev','--proc','/proc','--bind',str(F),str(F),'--bind',str(project),'/project']
inner=['/usr/bin/bwrap','--ro-bind','/','/','--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(node),str(node),'--bind',str(node),'/tmp/q_22c714e1','--bind','/project/n/o/94/live','/project/n/o/94/live','--chdir','/tmp/q_22c714e1']
# Prove that the old destination fails, while the live child remains writable.
probe=F/'probe.py';probe.write_text("from pathlib import Path\nPath('/project/n/o/94/live/probe').write_text('ok')\ntry:Path('/project/n/o/94/routing_selection.json').write_text('{}')\nexcept OSError as e:assert e.errno==30\nelse:raise AssertionError('project is writable')\n")
subprocess.run(outer+inner+[sys.executable,'-B',str(probe)],check=True)
decoded=base64.b64decode(json.loads((kit/'k/j.json').read_text())['payload']).decode()
start=decoded.index('set +e\n"${BW[@]}"');end=decoded.index('\n"${BW[@]}" "$PILOT_VENV/bin/python" -B -s "$Q_KIT/b/d.py"',start)
tail=decoded[start:end].replace('/usr/bin/python3',shlex.quote(sys.executable)).replace('"$Q_KIT/b/a.py"',shlex.quote(str(boundary))+' "$Q_KIT/b/a.py"')
prefix='set -uo pipefail\nBW=('+shlex.join(inner)+')\nPILOT_VENV='+shlex.quote(str(Path(sys.executable).parent.parent))+'\nQ_KIT='+shlex.quote(str(kit))+'\nQ_ROOT='+shlex.quote(str(node))+'\nQ_NS=/tmp/q_22c714e1\nexport Q_MODE=r SLURM_JOB_ID=94\n'
script=F/'run.sh';script.write_text(prefix+tail+'\n')
with (F/'shell.log').open('w') as log:
    p=subprocess.Popen(outer+['/bin/bash',str(script)],env={**os.environ,'TMPDIR':str(node/'tmp')},stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    while p.poll() is None:
        allocated=sum(x.stat().st_blocks*512 for x in D.rglob('*') if x.is_file() and not x.is_symlink() and x.stat().st_nlink==1)
        if allocated>175_000_000:
            os.killpg(p.pid,signal.SIGTERM);p.wait();raise RuntimeError('TEST_SPACE_GUARD:'+str(allocated))
        time.sleep(.5)
assert p.returncode==0,(p.returncode,(node/'q.log').read_text()[-4000:],(F/'shell.log').read_text())
value=J.load(node/'p/routing_selection.json');assert value==J.load(target/'o/94/routing_selection.json')
assert (target/'o/94/q.log').read_bytes()==(node/'q.log').read_bytes()
J.write(D/'MODE_R_TEST.json',dict(status='PASS',rows=value['rows'],regenerated_sha256=value['regenerated_sha256'],project_read_only=True,live_writable=True,publication_outside=True,returncode=p.returncode,scope='Native planner, staging validation, host checks and routing build; retained synthetic stores; tiny processor; hardlinked authenticated staging; P production equality requires Orchard.'))
print('mode r read-only project PASS',value['rows'],flush=True)
