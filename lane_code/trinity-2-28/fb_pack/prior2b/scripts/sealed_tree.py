from pathlib import Path
import hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parents[1];O=Path('/scratch/jjyeung/orch_n30/fb_pack/prior2');S=Path('/scratch/jjyeung/orch_n30/tree_rebuild15_w24l')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p))
seal=S/'out24j/TREE24J_SEAL.json';v=json.loads(seal.read_text());base=Path('/scratch/jjyeung/orch_n30/fb_pack/ro/orch_n30/tree_rebuild10_w/w24/out/TREE_FILES.sha256')
for line in base.read_text().splitlines():
 h,name=line.split('  ',1);src=O/'work/base'/name;assert sha(src)==h
 dest=W/'work/sealed_base'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
host=S/'out24j/HOST24J.patch'
r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(W/'work/sealed_base'),'-i',str(host)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
for name,h in v['files'].items():
 src=W/'work/sealed_base'/name;assert sha(src)==h,(name,sha(src),h)
 dest=W/'work/sealed_new'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
p=W/'out/PATCH_PRIOR.patch';r2=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(W/'work/sealed_new'),'-i',str(p)],capture_output=True,text=True);assert r2.returncode==0
out=dict(status='PASS',tree_sha256=v['tree_sha256'],files_verified=len(v['files']),reconstruction='Authenticated base 57a1f14d plus supplied HOST24J.patch, every resulting byte checked against 189df6ac inventory.',host_patch_output=r.stdout+r.stderr,prior_patch_output=r2.stdout+r2.stderr,inputs=[pin(x) for x in [Path(__file__),base,seal,host,p]])
(W/'out/SEALED_PATCH.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
