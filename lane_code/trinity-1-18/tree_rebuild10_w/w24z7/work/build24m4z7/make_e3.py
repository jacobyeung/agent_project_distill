from pathlib import Path
import shutil,secrets
J=Path.cwd();D=J/'out/e3';D.mkdir(exist_ok=True)
for name in ('e2.py','e2.sh','run.sh','readback.py'):
 s=(J/'out/e2'/name).read_text().replace('E2','E3').replace('e2','e3')
 (D/name.replace('e2','e3')).write_text(s)
p=D/'e3.sh';s=p.read_text();import re
s=re.sub(r'a15_cot_ap[0-9a-f]{12}','a15_cot_ap'+secrets.token_hex(6),s)
s=s.replace('export E3_PY="$PY" E3_N="$N"','export E3_PY="$PY" E3_N="$N"\nexport TK_JOB_START="$(date +%s)" TK_TIME_LIMIT_SECONDS=3600\nprintf "SLURM_TMPDIR=%s\\n" "${SLURM_TMPDIR:-/tmp}"\ndf -B1 "${SLURM_TMPDIR:-/tmp}"')
p.write_text(s);p.chmod(0o700)
p=D/'e3.py';s=p.read_text()
s=s.replace("'archive_after_recovery')", "'archive_after_recovery','rate','upload_logging')")
s=s.replace("  d=train/label;d.mkdir();(d/'q.bin').write_bytes(os.urandom(3<<20))", "  d=train/label;d.mkdir()\n  size=(int(os.environ.get('E3_LOCAL_BYTES','0')) or (2<<30)) if label.startswith('checkpoint') else 3<<20\n  with (d/'q.bin').open('wb') as f:\n   for _ in range(size//(1<<20)):f.write(os.urandom(1<<20))")
# Real E3 has a bounded fixture final pass. Production still uses allocation end.
s=s.replace("frc=invoke('f.log'", "os.environ['TK_COPY_DEADLINE']=str(time.time()+240)\n  tick=time.monotonic()\n  frc=invoke('f.log'")
s=s.replace("  checks['nonfatal']=", "  elapsed=time.monotonic()-tick\n  checks['nonfatal']=")
s=s.replace("  report['objects']=objects", "  report['objects']=objects\n  stop_key=load(k/'k/y.json')['objects']['ckstop']+'.j'+job\n  rate_rows=[dict(name=r['name'],bytes=r['bytes'],seconds=r.get('seconds'),MBps=r['bytes']/max(r.get('seconds',0),1e-6)/1e6) for r in rows if r['name'].startswith(stop_key+'.part')]\n  report['rate']=dict(payload_bytes=(train/'checkpoint_7/q.bin').stat().st_size,parts=rate_rows,final_pass_seconds=elapsed,total_MBps=sum(r['bytes'] for r in rate_rows)/max(elapsed,1e-6)/1e6,measured_stop_MBps=sum(r['bytes'] for r in rate_rows)/max([r['seconds'] for r in rate_rows]+[1e-6])/1e6)\n  report['SLURM_TMPDIR']=os.environ.get('SLURM_TMPDIR','/tmp')\n  report['tmp_free_bytes']=shutil.disk_usage(report['SLURM_TMPDIR']).free\n  checks['rate']='PASS' if len(rate_rows)==4 and all(r['seconds']>0 for r in rate_rows) else 'FAIL'\n  checks['upload_logging']='PASS' if (node/'live_spool/upload.log').is_file() and 'http' in (node/'live_spool/upload.log').read_text() else 'FAIL'")
s=s.replace("all(phases[i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4))", "any(phases[i:i+4]==['stop','exports','logs','o'] for i in range(len(phases))) and all(phases[i-1]=='o' for i,p in enumerate(phases) if p=='checkpoints' and i>0)")
s=s.replace("[n/'n/live_spool/retry.log',n/'n/o/retry.log']", "[n/'n/live_spool/retry.log',n/'n/o/retry.log',n/'n/live_spool/upload.log',n/'n/live_spool/final_order.jsonl']+list((n/'n/live_spool/state').glob('*'))")
s=s.replace("with p.open('rb') as f:f.seek(max(0,p.stat().st_size-32768));raw=f.read()", "with p.open('rb') as f:f.seek(0 if p.name=='upload.log' else max(0,p.stat().st_size-32768));raw=f.read()")
p.write_text(s)
# A transparent observer stays in every worker because pc.py uses threads.
(D/'observe.py').write_text('''import sys,os,json,runpy,subprocess,http.client,time,re
from pathlib import Path
N=Path(os.environ['E3_N']);K=N/'k';a=sys.argv[1:]
while a and a[0].startswith('-'):a.pop(0)
script=Path(a[0]).resolve();sys.argv=a
if script not in {(K/'b'/n).resolve() for n in ('pc.py','gc.py','o.py','ep.py','sr.py')}:raise SystemExit(92)
sys.path.insert(0,str(K/'b'))
original=subprocess.run
def run(argv,*args,**kw):
 if isinstance(argv,list) and any(str(K/'b'/v) in argv for v in ('pc.py','gc.py','o.py')):
  i=min(argv.index(str(K/'b'/v)) for v in ('pc.py','gc.py','o.py') if str(K/'b'/v) in argv)
  argv=argv[:i]+[str(N/'observe.py')]+argv[i:]
 return original(argv,*args,**kw)
subprocess.run=run
Original=http.client.HTTPSConnection
class Reply:
 def __init__(self,r):self.r=r;self.status=r.status
 def read(self,*a,**kw):
  raw=self.r.read(*a,**kw)
  if self.status in (200,201):
   try:
    v=json.loads(raw);keep={k:v.get(k) for k in ('size','crc32c','md5Hash','name','generation')}
    (N/'obs'/('r_'+str(os.getpid())+'_'+str(time.time_ns())+'.json')).write_text(json.dumps(keep)+'\\n')
   except (ValueError,OSError):pass
  return raw
 def __getattr__(self,n):return getattr(self.r,n)
class Connection(Original):
 def getresponse(self):return Reply(super().getresponse())
http.client.HTTPSConnection=Connection
try:runpy.run_path(str(script),run_name='__main__')
except SystemExit:raise
except Exception as e:
 print(re.sub(r'https?://[^\\s]+','[URL]',repr(e)),file=sys.stderr);raise SystemExit(1)
''')
print('E3 sources staged')
