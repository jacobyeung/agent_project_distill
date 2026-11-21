from pathlib import Path
import json,tarfile,hashlib
J=Path.cwd();E=J/'out/e2'
p=E/'e2.py';s=p.read_text()
s=s.replace("'response_fields','archive_while_full'","'final_order','response_fields','archive_while_full'")
s=s.replace("  orc=invoke('o.log',[k/'b/o.py',node,0,0])\n  frc=invoke('f.log',[k/'b/pc.py',k,node,job,'--final'])\n  checks['nonfatal']='PASS' if orc==frc==0", "  frc=invoke('f.log',[k/'b/pc.py',k,node,job,'--final','--status','0'])\n  checks['nonfatal']='PASS' if frc==0")
s=s.replace('len(objects)==12','len(objects)==16')
start=s.index('  # The adopted kit has no object label');end=s.index("  retry=node/'live_spool/retry.log'",start)
s=s[:start]+'''  archive=node/'o/o.tar';key=names['o']+'.j'+job
  expected=[key+f'.part{i:02d}-of-04' for i in range(4)]
  ar=[next((r for r in objects if r['name']==name),{}) for name in expected]
  done=node/'live_spool/state/gcs_o.done'
  receipt=load(done) if done.is_file() else {}
  good=(archive.is_file() and all(r.get('status')=='PASS' for r in ar)
        and sum(r.get('bytes',0) for r in ar)==archive.stat().st_size
        and receipt.get('sha256')==sha(archive) and receipt.get('object')==key
        and shutil.disk_usage(x).free==0)
  if good:
   with tarfile.open(archive) as t:good=load(node/'o/RESULT.json')==json.load(t.extractfile('RESULT.json'))
  checks['archive_while_full']='PASS' if good else 'FAIL'
  report['archive']=dict(local=archive.is_file(),bytes=archive.stat().st_size if archive.is_file() else 0,
      sha256=sha(archive) if archive.is_file() else None,objects=expected,free_bytes=shutil.disk_usage(x).free,
      result_inside=bool(good),cap_bytes=50_000_000)
  phases=[json.loads(s)['phase'] for s in (node/'live_spool/final_order.jsonl').read_text().splitlines()]
  report['final_order']=phases
  checks['final_order']='PASS' if phases and all(phases[i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4)) else 'FAIL'
''' +s[end:]
p.write_text(s)
p=E/'observe.py';s=p.read_text().replace("if isinstance(argv,list) and str(K/'b/gc.py') in argv:\n   i=argv.index(str(K/'b/gc.py'))", "if isinstance(argv,list) and any(str(K/'b'/name) in argv for name in ('gc.py','o.py')):\n   i=next(i for i,v in enumerate(argv) if v in (str(K/'b/gc.py'),str(K/'b/o.py')))")
p.write_text(s)
p=E/'readback.py';s=p.read_text().replace(" rows=json.load(open(a.report))['objects']"," report=json.load(open(a.report));rows=report['objects']\n archive=report['archive'];parts={}\n if report.get('status')!='PASS' or report['checks'].get('archive_while_full')!='PASS':raise ValueError('E24')")
s=s.replace('  passed=passed and good','  if row[\'name\'] in archive[\'objects\']:parts[row[\'name\']]=raw\n  passed=passed and good')
s=s.replace(' return 0 if passed and len(rows)==12 else 1'," raw=b''.join(parts.get(name,b'') for name in archive['objects'])\n good=(len(parts)==4 and len(raw)==archive['bytes'] and hashlib.sha256(raw).hexdigest()==archive['sha256'])\n print(json.dumps(dict(archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),status='PASS' if good else 'FAIL')))\n return 0 if passed and good and len(rows)==16 else 1")
p.write_text(s)
p=E/'e2.sh';s=p.read_text().replace('set -euo pipefail','# The final pass requires the four o parts while X is full.\nset -euo pipefail');p.write_text(s)
with tarfile.open(E/'k.tgz','w:gz') as t:
 for p in sorted((J/'out/kit_n').rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(J/'out/kit_n')),recursive=False)
pins={name:hashlib.sha256((E/name).read_bytes()).hexdigest() for name in ('e2.py','observe.py','run.sh','k.tgz')}
(E/'pins.json').write_text(json.dumps(pins,sort_keys=True,indent=2)+'\n')
print('E2 updated', (E/'k.tgz').stat().st_size)
