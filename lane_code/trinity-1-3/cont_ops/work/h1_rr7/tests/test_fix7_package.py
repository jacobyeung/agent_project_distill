"""Check opaque payload integrity and the guarded patch against local copies."""
import base64,hashlib,json,re,subprocess,sys,tempfile,zlib
from pathlib import Path
H=Path(__file__).resolve().parents[1]
out=Path(tempfile.mkdtemp(prefix='package_',dir=H/'evidence/fix7_selection'))
s=(H/'build/q.sh').read_text();assert len(s.encode())<1_000_000
subprocess.run(['/bin/bash','-n',str(H/'build/q.sh')],check=True)
blob=re.search(r"base64.b64decode\('([^']+)'\)",s)[1]
raw=zlib.decompress(base64.b64decode(blob));expected=re.search(r"hexdigest\(\)!='([a-f0-9]+)'",s)[1]
assert hashlib.sha256(raw).hexdigest()==expected
files=json.loads(raw)
assert files['v.py']==(H/'tools/selection_check.py').read_text()
assert files['b.json']==(H/'payload/d_f232d4160d75b582.json').read_text()
assert files['c.json']==(H/'payload/7.json').read_text()
assert '--unshare-net' in s and 'nice -n 19' in s and 'HF_HUB_OFFLINE=1' in s
# Run the exact stdlib bootstrap with local argv; no bubblewrap or login invocation.
w=out/'w';w.mkdir();b=out/'b';b.mkdir()
import os
os.link(H/'payload/t_9588661986650d29.tar',b/'t_9588661986650d29.tar')
start=s.index("<<'P' >\"$W/b.log\" 2>&1\n")+len("<<'P' >\"$W/b.log\" 2>&1\n")
bootstrap=s[start:s.index('\nP\n',start)]
subprocess.run([sys.executable,'-I','-B','-',str(w),str(b)],input=bootstrap,text=True,check=True,capture_output=True)
assert (w/'v.py').read_text()==files['v.py']
corrupt=bootstrap.replace(blob,('A' if blob[0]!='A' else 'B')+blob[1:])
f=out/'bad';f.mkdir()
r=subprocess.run([sys.executable,'-I','-B','-',str(f),str(b)],input=corrupt,text=True,capture_output=True)
assert r.returncode!=0 and not list(f.iterdir())
# Check visible shell/Python literals after excluding authenticated opaque data.
visible=s.replace(blob,'OPAQUE')
for prefix in ['/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung','/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung']:
 visible=visible.replace(prefix,'/sealed')
forbidden=re.compile(r'(?i)(?<![a-z0-9])(?:distill|vsi|revsi|scannet|arkit|sft|h1|r0|qwen|cot)(?![a-z0-9])')
assert not forbidden.search(visible)
# Preserve earlier test evidence: redirect the existing patch regression's output.
src=(H/'tests/test_config_patch.py').read_text().replace("H/'evidence/fix6_patch'",repr(str(out/'patch')))
src=src.replace("OUT="+repr(str(out/'patch')),"OUT=Path("+repr(str(out/'patch'))+")")
src=src.replace('evidence/fix6_patch_manifest.json','evidence/fix7_patch_manifest.json')
exec(compile(src,'<local-patch-regression>','exec'),{'__file__':str(H/'tests/test_config_patch.py')})
# Every upload member and immutable payload pin must agree.
u=json.loads((H/'UPLOAD.json').read_text())
for row in u['files']:assert hashlib.sha256((H/'payload'/row['name']).read_bytes()).hexdigest()==row['sha256']
assert hashlib.sha256((H/'build'/u['archive']).read_bytes()).hexdigest()==u['sha256']
(H/'evidence/fix7_selection/package_tests.json').write_text(json.dumps(dict(status='PASS',path=str(out),script_bytes=len(s.encode()),bootstrap='PASS',corrupt_blob_refused=True,patch_cases=7,visible_names='PASS',login_bwrap='NOT RUN'),indent=2)+'\n')
print(out)
