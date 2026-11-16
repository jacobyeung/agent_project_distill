"""Check unchanged identities, deterministic rebuilds, transport and patch bytes."""
import base64,hashlib,json,subprocess,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads((H/p).read_text())
before=load('evidence/fix5_before/hashes.json')
assert load('ids.json')==load('evidence/fix5_before/ids.json')
for name in ('ids.json','TOKENS_H1.json','tests/RERUN_CHAIN.sh','runtime/jb.sh','payload/jb.sh','payload/7.json','payload/4.json','payload/over.json','payload/r.py','payload/d.py','build/fx/SHA256SUMS.txt'):
    assert sha(H/name)==before[name],name
for n,h in before.items():
    if n.startswith('payload/') and n not in ('payload/g.sh','payload/sums.txt'):assert sha(H/n)==h,n
records=[]
for _ in range(2):
    for script in ('tools/make_orchard.py','tools/build_gate_patch.py'):
        subprocess.run([sys.executable,'-B',script],cwd=H,check=True)
    records.append({n:sha(H/n) for n in ('UPLOAD.json','orch_h1.sh','payload/g.sh','payload/sums.txt','build/g_patch.sh')})
assert records[0]==records[1]
up=load('UPLOAD.json')
assert sha(H/'build'/up['archive'])==up['sha256']
with tarfile.open(H/'build'/up['archive']) as tf:
    names=[]
    for m in tf:
        names.append(m.name)
        assert m.isfile() and m.mode==0o600 and (m.uid,m.gid,m.uname,m.gname,m.mtime)==(0,0,'','',0)
        assert tf.extractfile(m).read()==(H/'payload'/m.name).read_bytes()
    assert names==sorted(names)
script=(H/'orch_h1.sh').read_text()
b64=script.split("<<'B64'\n",1)[1].split('\nB64\n',1)[0]
assert hashlib.sha256(base64.b64decode(b64)).hexdigest()==up['sha256']
subprocess.run(['sha256sum','-c','sums.txt'],cwd=H/'payload',check=True,stdout=subprocess.DEVNULL)
for n in ('payload/g.sh','build/g_patch.sh','orch_h1.sh'):
    subprocess.run(['/bin/bash','-n',str(H/n)],check=True)
assert (H/'build/g_patch.sh').stat().st_size<1_000_000
# The trainer bytes and every available derived fixture member remain pinned.
ids=load('ids.json');assert sha(H/'payload'/ids['trainer']['file'])==ids['trainer']['sha256']
missing=[]
for line in (H/'build/fx/SHA256SUMS.txt').read_text().splitlines():
    h,n=line.split('  ',1);p=H/'build/fx'/n
    if p.is_file():assert sha(p)==h,n
    else:missing.append(n)
assert len(missing)==2
result=dict(status='PASS',deterministic=records[0],upload=up['sha256'],identity=ids['identity'],contract=ids['contract'],fixture_manifest=ids['fixture_manifest'],unchanged_payload_except_gate_and_sums=True,chain_runner_unchanged=True,archive_metadata='PASS',embedded_transport='PASS',sums='PASS',fixture_missing_payloads=missing)
(H/'evidence/fix5/package.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
