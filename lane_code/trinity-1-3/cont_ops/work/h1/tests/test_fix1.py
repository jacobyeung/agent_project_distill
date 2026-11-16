"""CPU-only regression checks for review round 1; no sockets or remote calls."""
import ast,copy,difflib,hashlib,io,json,os,stat,subprocess,sys,tarfile,shlex
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(H/'tools'))
import derive_kit_h1 as dk
from private_paths import CHECK
D=Path('/scratch/jjyeung/orch_n30/review_h1pkt/work/d0')
root=H/'evidence/fix1_tests';root.mkdir(mode=0o700)
results={}
def run(script):
 return subprocess.run(['/bin/bash','-c',script],env=dict(os.environ,SLURM_JOB_ID='1'),capture_output=True,text=True)
# Run every executable entry through its actual first permission check, before any other action.
for n in ['orch_h1.sh','fin_h1.sh','payload/o.sh','payload/g.sh','payload/z.sh','payload/s.sh','runtime/jb.sh']:
 b=root/(Path(n).stem+'_mode');b.mkdir(mode=0o755);b.chmod(0o755)
 script=(H/n).read_text().replace('/project/community/jjyeung/okh7',str(b))
 p=root/(Path(n).stem+'.sh');p.write_text(script)
 before=sorted(b.iterdir());rc=subprocess.run(['/bin/bash',str(p)],env=dict(os.environ,SLURM_JOB_ID='1'),capture_output=True,text=True)
 assert rc.returncode==3 and 'chmod 700' in rc.stderr,(n,rc.stderr)
 assert sorted(b.iterdir())==before and stat.S_IMODE(b.stat().st_mode)==0o755
module=ast.parse((H/'payload/r.py').read_text())
fn=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='private')
scope=dict(stat=stat,shlex=shlex)
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<permission-test>','exec'),scope)
try:scope['private'](b)
except SystemExit as e:assert 'chmod 700' in str(e)
else:raise AssertionError('direct Python mode check accepted 0755')
results['all_entrypoints_refuse_public_parent_without_changes']=True
# Run the exact jb.sh directory preflight with only physical locations relocated.
s=(H/'runtime/jb.sh').read_text();block=s[s.index('# BEGIN directory preflight'):s.index('# END directory preflight')]
for foreign in ('deadbeef','.deadbeef',None):
 b=root/('foreign_'+foreign if foreign else 'clean');b.mkdir(mode=0o700)
 o=b/'o';o.mkdir(mode=0o700);kh=o/'x';kh.mkdir(mode=0o700)
 tmp=b/'tmp';tmp.mkdir(mode=0o700);nl=tmp/'a_17c4ffa4'
 if foreign:
  (nl/'runs'/foreign).mkdir(parents=True,mode=0o700)
  nl.chmod(0o700);(nl/'runs').chmod(0o700)
 script=CHECK.replace('/project/community/jjyeung/okh7',str(o))+'\n'+f'KH={kh}; RUN={nl}/runs/17c4ffa4; RS={o}/r/12345678\n'+block.replace('/tmp/jjyeung',str(tmp))
 rc=run(script)
 if foreign:
  assert rc.returncode==3 and 'foreign run' in rc.stderr,rc.stderr
  assert not (nl/'runs/17c4ffa4').exists() and not (o/'r').exists()
 else:
  assert rc.returncode==0,rc.stderr
  for p in (nl,nl/'runs',nl/'runs/17c4ffa4',o/'r/12345678'):assert stat.S_IMODE(p.stat().st_mode)==0o700
results['foreign_run_refusal_before_writes_and_private_creation']=True
la=json.loads((H/'build/fx/k/launch.json').read_text())
assert la['run_directory']=='/tmp/jjyeung/a_17c4ffa4/runs/17c4ffa4'
assert stat.S_IMODE((H/'build/fx').stat().st_mode)==0o700
for n in ['b/c.sh','b/p0.sh','b/r.sh','job.sh']:
 assert '/tmp/jjyeung/okit_' not in (H/'build/fx'/n).read_text()
c=(H/'build/fx/b/c.sh').read_text()
assert 'K=8865619b' in c and 'NR=/tmp/jjyeung/a_17c4ffa4/runs' in c
assert 'tarf="$S/../up/' in c and 'obj="q8/$K/' in c
results['all_physical_roots_isolated_object_namespace_preserved']=True
# Missing authorization is refused before creating a partial output.
over=json.loads((H/'build/over_fx.json').read_text());del over['add_k']['4.json']
try:dk.derive(D/'kitfull',root/'missing',over)
except ValueError as e:assert 'requires add_k 4.json' in str(e)
else:raise AssertionError('missing authorization admitted')
assert not (root/'missing').exists()
results['missing_authorization_refused_early']=True
# Execute the final derive/identity check with a hostile derive result.
s=(H/'payload/r.py').read_text();start=s.index(" w(B/'ready.json',o)");end=s.index(' # Compare the complete',start)
fragment='\n'.join(x[1:] for x in s[start:end].splitlines())
for ident,accepted in [('wrong',False),('right',True)]:
 writes=[];scope=dict(B=root,KH=root,base=root,o={},ids={'identity':'right'},private=lambda p:None,w=lambda p,v:writes.append(p.name),dk=SimpleNamespace(derive=lambda *a:{'config_identity':ident}))
 try:exec(fragment,scope)
 except AssertionError:assert not accepted
 else:assert accepted
 assert ('result.json' in writes)==accepted
results['final_identity_checked_before_result_or_compare']=True
# Each final entry checks the immutable packet before interpreting operator evidence.
for n in ['z.sh','s.sh']:
 text=(H/'payload'/n).read_text();assert text.index('sha256sum -c sums.txt')<text.index('python3')
results['final_entries_recheck_checksums']=True
# Corruption must actually stop the checksum command used by both entries.
b=root/'sums';b.mkdir();(b/'item').write_text('altered');(b/'sums.txt').write_text(hashlib.sha256(b'original').hexdigest()+'  item\n')
assert subprocess.run(['sha256sum','-c','sums.txt'],cwd=b,capture_output=True).returncode!=0
# Exercise the actual routing copy function using a small sealed fixture.
module=ast.parse(s);func=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='stage_archive')
b=root/'copy';b.mkdir();base=b/'base';(base/'k').mkdir(parents=True);bundle=b/'bundle';bundle.mkdir()
receipt='ap/5e1d07a4/f/h/r16/receipt.json';arc=b/'input.tar';data=b'{}\n'
with tarfile.open(arc,'w') as tf:
 m=tarfile.TarInfo(receipt);m.size=len(data);tf.addfile(m,io.BytesIO(data))
record={'tars':[{'parts':[str(arc)],'files':{receipt:hashlib.sha256(data).hexdigest()}}]}
(base/'k/0.json').write_text(json.dumps(record));(base/'SHA256SUMS.txt').write_text(dk.sha(base/'k/0.json')+'  k/0.json\n')
scope=dict(Path=Path,hashlib=hashlib,tarfile=tarfile,B=bundle,base=base,dk=SimpleNamespace(sha=dk.sha,SEALED_MANIFEST=dk.sha(base/'SHA256SUMS.txt')),load=lambda p:json.loads(p.read_text()),manifest=lambda p:{'k/0.json':dk.sha(p/'k/0.json')},w=dk.write)
exec(compile(ast.Module(body=[func],type_ignores=[]),'<copy-test>','exec'),scope);scope['stage_archive']()
pin=json.loads((bundle/'a.json').read_text());assert pin['sha256']==dk.sha(arc)==dk.sha(bundle/pin['file'])
assert pin['files']==record['tars'][0]['files']
# A self-consistent source archive with wrong member bytes still fails its sealed pin.
bad=b/'bad';bad.mkdir();scope['B']=bad
record['tars'][0]['files'][receipt]='0'*64;(base/'k/0.json').write_text(json.dumps(record))
(base/'SHA256SUMS.txt').write_text(dk.sha(base/'k/0.json')+'  k/0.json\n');scope['dk'].SEALED_MANIFEST=dk.sha(base/'SHA256SUMS.txt')
try:scope['stage_archive']()
except AssertionError:pass
else:raise AssertionError('corrupt routing member accepted')
assert not (bad/'a.json').exists()
results['opaque_routing_copy_digest_and_member_checks']=True
assert all('canary-2' not in v for v in json.loads((H/'payload/4.json').read_text())['conditions'])
results['irrelevant_resume_condition_removed']=True
(H/'evidence/fix1_tests.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
