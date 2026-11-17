from pathlib import Path
import io,json,tarfile,sys,tempfile,subprocess,hashlib
W=Path.cwd();O=W/'out';sys.path.insert(0,str(O/'src'))
from orchard_h10.common import canonical,sha,write
r=Path(json.loads((O/'RETURN_MEMBERS.json').read_text())['root']);members=json.loads((O/'RETURN_MEMBERS.json').read_text())['members']
public=json.loads((O/'package/0.json').read_text());inputs=json.loads((O/'inputs_tower.json').read_text())
identity=json.loads((r/'metadata/IDENTITY.json').read_text());identity.update(plan=public['plan_sha256'],inputs=canonical({k:v for k,v in inputs.items() if k!='resume'}),operator_sha256=sha(O/'tower_sequence.py'))
root=Path(tempfile.mkdtemp(prefix='return_',dir=W/'work/tmp'));missing=next(n for n in members if n.endswith('/items.jsonl'))
for label,omit in [('full',None),('missing',missing)]:
 archive=root/(label+'.tgz')
 with tarfile.open(archive,'w:gz') as t:
  for name in members:
   if name==omit:continue
   raw=(json.dumps(identity)+'\n').encode() if name=='metadata/IDENTITY.json' else (r/name).read_bytes()
   m=tarfile.TarInfo(name);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
 receipt=root/(label+'.json');write(receipt,dict(synthetic=False,plan_sha256=public['plan_sha256'],archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,complete=True,status='COMPLETE'))
 result=subprocess.run([sys.executable,'-B',str(O/'unpack_return.py'),'--archive',str(archive),'--exit',str(receipt),'--out',str(root/label)],capture_output=True,text=True)
 if omit:
  assert result.returncode!=0 and ('Started segment has no journal' in result.stderr or 'Started read has no journal' in result.stderr),result.stderr
 else:
  assert result.returncode==0,result.stderr
  assert len(list((root/label).rglob('items.jsonl')))==1
 print(label,result.returncode,result.stdout.strip() or result.stderr.splitlines()[-1])
write(O/'RETURN_CLI.json',dict(passed=True,root=str(root),full_journals=1,missing_journal_refused=True))
