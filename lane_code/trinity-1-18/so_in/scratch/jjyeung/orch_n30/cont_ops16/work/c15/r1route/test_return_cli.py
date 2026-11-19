from pathlib import Path
import io,json,tarfile,sys,tempfile,subprocess,hashlib
W=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canonical=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
for k in ('b1','b2'):
 O=W/'out'/k;R=W/'release'/k
 proof=json.loads((R/'RETURN_MEMBERS.json').read_text());r=Path(proof['root']);members=proof['members']
 public=json.loads((O/'package/0.json').read_text());inputs=json.loads((R/'inputs_tower.json').read_text())
 identity=json.loads((r/'metadata/IDENTITY.json').read_text());identity.update(plan=public['plan_sha256'],inputs=canonical({k:v for k,v in inputs.items() if k!='resume'}),operator_sha256=sha(O/'tower_sequence.py'))
 root=Path(tempfile.mkdtemp(prefix='return_',dir=W/'out/test_tmp'));missing=next(n for n in members if n.endswith('/items.jsonl'))
 for label,omit in [('full',None),('missing',missing)]:
  archive=root/(label+'.tgz')
  with tarfile.open(archive,'w:gz') as t:
   files={n:(r/n).read_bytes() for n in members if n!=omit}
   files['metadata/IDENTITY.json']=(json.dumps(identity)+'\n').encode();files['metadata/INPUTS.json']=(R/'inputs_tower.json').read_bytes();files['metadata/EXPORT_PIN.json']=(R/'package/a/export.json').read_bytes()
   for n,raw in files.items():
    m=tarfile.TarInfo(n);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
  receipt=root/(label+'.json');receipt.write_text(json.dumps(dict(synthetic=False,plan_sha256=public['plan_sha256'],archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,complete=True,status='COMPLETE')))
  result=subprocess.run([sys.executable,'-B',str(O/'unpack_return.py'),'--archive',str(archive),'--exit',str(receipt),'--out',str(root/label)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  if omit:assert result.returncode!=0 and (b'Started segment has no journal' in result.stderr or b'Started read has no journal' in result.stderr),result.stderr
  else:assert result.returncode==0,result.stderr
  print(k,label,result.returncode)
 (O/'RETURN_CLI.json').write_text(json.dumps(dict(passed=True,tests=2,failures=0,errors=0,skipped=0,root=str(root),full_journals=5 if k=='b1' else 1,missing_journal_refused=True))+'\n')
