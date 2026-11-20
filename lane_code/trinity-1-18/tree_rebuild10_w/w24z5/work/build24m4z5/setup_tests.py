from pathlib import Path
import os,shutil,json,hashlib,tarfile,sys,secrets
J=Path.cwd();D=J/'work/build24m4z5';K=J/'out/kit_n';W=J/'work/enospc5'
for n in ('b/pc.py','b/pc.sh','b/o.py'):shutil.copy2(K/n,J/'out/kit_n_go'/n)
# Create new test fixtures; preserve all inherited output.
W.mkdir()
for n in ('runtime.py','fake_gc_run.py','j2_helper_new.py','retest.py','check_current.py','signals_current.py','wrapper_prefix2.py'):
 s=(J/'work/enospc4_final'/n).read_text().replace('out/jn2.sh','out/jn3.sh')
 s=s.replace("i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4)","i:i+5]==['stop','exports','logs','o','checkpoints'] for i in range(0,len(phases),5)")
 if n=='runtime.py':
  s=s.replace("   a=list(a);a[a.index(str(K/'b/gc.py'))]=str(W/'fake_gc_run.py')", "   i=a.index(str(K/'b/gc.py'));a=[sys.executable,'-B',str(W/'fake_gc_run.py'),*a[i+1:]]")
 if n=='check_current.py':s=s.replace("c=m.Copier(K,N,'24008',writer=W/'fake_gc_run.py')","c=m.Copier(K,N,'24008',writer=W/'fake_gc_run.py');c.exit_status=None")
 (W/n).write_text(s)
for n in ('bin','tmp','logs','mnt','mnt4','mnt5','node'):(W/n).mkdir()
shutil.copytree(K,W/'kit')
(W/'bin/python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(W/'runtime.py')+' "$@"\n');(W/'bin/python3').chmod(0o755)
for name in ('current_final_tests.py','archive_final_tests.py','legacy_final_tests.py'):
 s=(J/'work/build24m4z4'/name).read_text().replace('/w24z4','/w24z5').replace('build24m4z4','build24m4z5').replace('enospc4_final','enospc5').replace('work/enospc4/', 'work/enospc5/')
 if name=='current_final_tests.py':s=s.replace('  c.checkpoints();c.stop_checkpoint()', '  c.final_pass=True;c.stop_checkpoint();c.checkpoints()')
 if name=='archive_final_tests.py':
  s=s.replace(" return C.Copier(k,n,'41',writer=D/'writer.py')", "\n for name in ('o.py','z.py','wh.json','pc.py'):\n  (k/'b').mkdir(exist_ok=True);shutil.copy2(K/'b'/name,k/'b'/name)\n for name in ('g.json',):shutil.copy2(K/'k'/name,k/'k'/name)\n c=C.Copier(k,n,'41',writer=D/'writer.py');c.final_pass=True;return c")
 if name=='legacy_final_tests.py':
  s=s.replace("'m100','mstop','mstopB','mstopC','ckstop','o'", "'m100','m200','m400','m600','m800','m1000','mstop','mstopB','mstopC','ckstop','o'")
  s=s.replace("    return C.Copier(kit,node,'41',home=home),root", "    (kit/'b/writer.py').write_text(WRITER)\n    c=C.Copier(kit,node,'41',home=home,writer=kit/'b/writer.py');c.final_pass=True;return c,root")
  s=s.replace("    (kit/'b/gc.py').write_text(WRITER)", "    (kit/'b/gc.py').write_bytes((L/'out/kit_n/b/gc.py').read_bytes())")
  # TERM test checks bounded shutdown and final log publication without transport.
  s=s.replace("p=subprocess.Popen(['/bin/bash',str(script)],stdout=log,stderr=subprocess.STDOUT)", "p=subprocess.Popen(['/bin/bash',str(script)],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'SLURM_JOB_END_TIME':str(time.time()+605)})")
  (D/'legacy_final').mkdir()
 (D/name).write_text(s)
# E3 retains every E2 assertion and adds a four-part rate payload.
E=J/'out/e3';E.mkdir()
for p in (J/'out/e2').iterdir():
 if p.name=='k.tgz':continue
 name=p.name.replace('e2','e3').replace('E2','E3')
 s=p.read_text().replace('e2','e3').replace('E2','E3')
 if name=='e3.sh':s=s.replace('a15_cot_apf482d730ca91','a15_cot_ap'+secrets.token_hex(6))
 if name=='e3.py':
  s=s.replace("CHECKS=", "RATE_BYTES = 2 << 30\n\nCHECKS=")
  s=s.replace("'archive_after_recovery')", "'archive_after_recovery','rate')")
  s=s.replace("  receipts=node/", """  rate_dir=node/'rate';rate_dir.mkdir();payload=rate_dir/'q.bin'
  with payload.open('wb') as f:
   left=RATE_BYTES
   while left:
    raw=os.urandom(min(left,1<<20));f.write(raw);left-=len(raw)
  rate_started=time.monotonic()
  rate_rc=invoke('rate.log',[k/'b/pc.py',k,node,job,'--payload',payload])
  rate_seconds=time.monotonic()-rate_started
  report['rate_bytes']=RATE_BYTES
  report['SLURM_TMPDIR']=os.environ.get('SLURM_TMPDIR')
  report['tmp_free_bytes']=shutil.disk_usage(n).free
  report['tmp_df']=subprocess.run(['df','-B1',str(n)],capture_output=True,text=True,check=True).stdout
  receipts=node/""",1)
  s=s.replace('len(objects)==16','len(objects)==20')
  s=s.replace("  report['receipts']=", """  rate_rows=[r for r in rows if r['name'].startswith(names['ck01']+'.j'+job+'.part')]
  report['rate']=dict(bytes=RATE_BYTES,seconds=rate_seconds,MBps=RATE_BYTES/max(rate_seconds,.001)/1e6,
   parts=[dict(name=r['name'],bytes=r['bytes'],seconds=r['seconds'],MBps=r['bytes']/max(r['seconds'],.001)/1e6) for r in rate_rows])
  checks['rate']='PASS' if rate_rc==0 and len(rate_rows)==4 and sum(r['bytes'] for r in rate_rows)==RATE_BYTES else 'FAIL'
  report['receipts']=""")
  s=s.replace("i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4)","i:i+5]==['stop','exports','logs','o','checkpoints'] for i in range(0,len(phases),5)")
 if name=='observe.py':
  s=s.replace("if script.name=='gc.py':", "if script.name=='gc.py' or '--writer' in args:")
  s=s.replace("   i=next(i for i,v in enumerate(argv) if v in (str(K/'b/gc.py'),str(K/'b/o.py')))\n   argv=argv[:i]+[str(N/'observe.py')]+argv[i:]", "   i=next(i for i,v in enumerate(argv) if v in (str(K/'b/pc.py'),str(K/'b/gc.py'),str(K/'b/o.py')))\n   argv=argv[:i]+[str(N/'observe.py')]+argv[i:]")
 if name=='readback.py':s=s.replace('len(rows)==16','len(rows)==20')
 (E/name).write_text(s)
 (E/name).chmod(p.stat().st_mode&511)
print('Prepared fixtures and E3 sources')
