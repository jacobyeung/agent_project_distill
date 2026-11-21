import json,os,subprocess,sys,time
from pathlib import Path
args=sys.argv[1:]
while args and args[0] in ('-I','-s','-B'):args.pop(0)
if args[0]=='-':
 if os.environ.get('MIRROR_FAIL')=='1':sys.exit(73)
 os.execv(sys.executable,[sys.executable,'-I','-s','-B',*args])
p=Path(args[0]);a=args[1:];F=Path(os.environ['FIXTURE'])
if p.name=='j8.py':
 if a[0]=='b':print(F/'bin/bw');sys.exit(0)
 if a[0]=='p':
  node=Path(a[1]);assert 'work exit '+os.environ['WORK_RC'] in (node/'j2.log').read_text()
  if os.environ.get('MIRROR_FAIL')!='1':
   state=json.loads((Path(a[2]+'_live')/'live.json').read_bytes());assert state['phase']=='final'
  os.execv(sys.executable,[sys.executable,'-I','-s','-B',str(p),*a])
if p.name in ('j2.py','v.py'):sys.exit(0)
if p.name=='resolve.py':
 Path(a[a.index('--output')+1]).write_text('{}');sys.exit(0)
if p.name=='l.py':sys.stdout.write(sys.stdin.read());sys.exit(0)
if p.name=='x.py':
 node=Path(a[2]);(node/'ev').mkdir(exist_ok=True)
 (node/'ev/q.log').write_bytes(b'q'*300000+b'END')
 (node/'ev/q.steps').write_text('done')
 (node/'ev/large').write_bytes(os.urandom(3600000))
 (node/'p/q/b').mkdir(parents=True);(node/'p/q/b/receipt.json').write_text('{"ok":true}')
 time.sleep(.15);sys.exit(int(os.environ['WORK_RC']))
if p.name=='dbb3.py':sys.exit(1)
raise AssertionError(args)
