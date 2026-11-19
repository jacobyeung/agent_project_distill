from pathlib import Path
import hashlib,json,subprocess,tempfile
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=json.loads((O/'FILES_TOUCHED.json').read_text())['files'];changes={e['path']:e['new_sha256'] for e in rows};inputs={str(O/'FILES_TOUCHED.json'):sha(O/'FILES_TOUCHED.json'),str(Path(__file__).resolve()):sha(__file__)};results=[]
base={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (O/'TREE_FILES.sha256').read_text().splitlines()}
live=json.loads(Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/out24j/TREE24J_SEAL.json').read_text())['files']
for src,dest,patch,files in [('base','base_apply','PATCH_DONOR2.patch',base),('donor_orig','delta_apply','PATCH_DONOR2_DELTA.patch',{**base,**{e['path']:e['donor_sha256'] for e in rows}}),('live_base','live_apply','PATCH_DONOR2.patch',live)]:
 tree=Path(tempfile.mkdtemp(prefix=dest+'_',dir=W/'work'))
 staged=base if src=='donor_orig' else files
 stage_source='base' if src=='donor_orig' else src
 for n,h in staged.items():
  p=W/'work'/stage_source/n;assert sha(p)==h;q=tree/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
 prerequisite=None
 if src=='donor_orig':
  original=W.parent/'donor/out/PATCH_DONOR.patch';inputs[str(original)]=sha(original)
  assert sha(original)=='fff484d7c59e992f227ed53fd12c07b565f42ab9eaf629e44c4523621bc983be'
  cmd=['patch','--fuzz=0','--batch','-p1','-d',str(tree),'-i',str(original)]
  first=subprocess.run(cmd,text=True,capture_output=True)
  assert first.returncode==0 and 'fuzz' not in first.stdout and 'offset' not in first.stdout,first.stdout
  assert all(sha(tree/n)==h for n,h in files.items())
  prerequisite=' '.join(cmd)
 pp=O/patch;inputs[str(pp)]=sha(pp)
 command=['patch','--fuzz=0','--batch','-p1','-d',str(tree),'-i',str(pp)]
 r=subprocess.run(command,text=True,capture_output=True);assert r.returncode==0,(src,r.stdout,r.stderr)
 assert 'fuzz' not in r.stdout and 'offset' not in r.stdout,r.stdout
 expected={**files,**changes};actual={n:sha(tree/n) for n in expected};assert actual==expected
 log=O/(dest+'.log');log.write_text(r.stdout+r.stderr)
 results.append(dict(source=src,prerequisite_command=prerequisite,command=' '.join(command),files_verified=len(expected),zero_fuzz=True,zero_offset=True,unchanged_files_verified=len(set(files)-set(changes)),log_sha256=sha(log)))
inputs[str(O/'STAGING.json')]=sha(O/'STAGING.json');inputs[str(O/'LIVE_VERIFY.json')]=sha(O/'LIVE_VERIFY.json')
(O/'PATCH_APPLICATION.json').write_text(json.dumps(dict(input_sha256=inputs,status='PASS',applications=results,command='python code/verify_patches.py'),indent=2)+'\n')
print('Full, delta and live patch applications verified without fuzz or offset')
