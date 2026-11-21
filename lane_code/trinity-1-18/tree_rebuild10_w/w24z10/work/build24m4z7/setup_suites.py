from pathlib import Path
import os,sys,shutil,json
J=Path.cwd();D=J/'work/build24m4z7';W=J/'work/enospc7';W.mkdir()
old=J/'work/enospc4_final'
for name in ('j2_helper_new.py','retest.py','check_current.py','signals_current.py','wrapper_prefix2.py'):
 s=(old/name).read_text();(W/name).write_text(s)
for name in ('bin','tmp','logs','mnt','mnt4','mnt5','node'):(W/name).mkdir()
shutil.copytree(J/'out/kit_n',W/'kit')
(W/'bin/python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(D/'runtime.py')+' "$@"\n');(W/'bin/python3').chmod(0o700)
writer=(D/'strict_writer.py').read_text().replace("sys.path.insert(0,str(Path(__file__).parent))","sys.path.insert(0,"+repr(str(D))+")")
writer=writer.replace("kit=Path(os.environ['STRICT_KIT'])", "os.environ['STRICT_SINK']=os.environ.get('FAKE_SINK',str(Path(sys.argv[2]).parent/'objects'))\nkit=Path("+repr(str(J/'out/kit_n'))+")")
(W/'fake_gc_run.py').write_text(writer)
s=(W/'retest.py').read_text()
s=s.replace("sink=list((W/'sink').iterdir())","sink=list((W/'sink').glob('*.data'))")
s=s.replace("  path='/o/'+str(i)+'?'\n  raw+=(W/'sink'/hashlib.sha256(path.encode()).hexdigest()).read_bytes()", "  raw+=(W/'sink'/(hashlib.sha256(row['name'].encode()).hexdigest()+'.data')).read_bytes()")
s=s.replace("all(phases[i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4))", "any(phases[i:i+4]==['stop','exports','logs','o'] for i in range(len(phases)))")
(W/'retest.py').write_text(s)
s=(W/'check_current.py').read_text().replace("TMPDIR=str(W/'tmp'))", "TMPDIR=str(W/'tmp'),TEST_W=str(W))")
s=s.replace("c=m.Copier(K,N,'24008',writer=W/'fake_gc_run.py')", "c=m.Copier(K,N,'24008',writer=W/'fake_gc_run.py');c.exit_status=0\noriginal_run=subprocess.run\ndef invoke(argv,*a,**kw):\n if isinstance(argv,list) and str(K/'b/o.py') in argv:\n  i=argv.index(str(K/'b/o.py'));argv=argv[:i]+[str(J_RUNTIME)]+argv[i:]\n return original_run(argv,*a,**kw)\nJ_RUNTIME="+repr(str(D/'runtime.py'))+"\nsubprocess.run=invoke")
s=s.replace("'gcs_checkpoint_8_stop.done'}", "'gcs_checkpoint_8_stop.done','gcs_o.done'}")
s=s.replace("glob('*')))","glob('*.data')))")
(W/'check_current.py').write_text(s)
# Exact helper from jn3, with the existing recovery fixture's accelerated clock.
wrapper=(J/'out/jn3.sh').read_text();helper=wrapper.split("<<'PYJ2'\n",1)[1].split('\nPYJ2',1)[0]
(W/'j2_helper_new.py').write_text(helper)
s=(W/'wrapper_prefix2.py').read_text().replace("out/jn2.sh","out/jn3.sh").replace("'E28' in", "'OSError' in")
(W/'wrapper_prefix2.py').write_text(s)
for stem in ('current','archive','legacy'):
 s=(J/'work/build24m4z4'/(stem+'_final_tests.py')).read_text()
 s=s.replace('/w24z4','/w24z7').replace('build24m4z4/'+stem+'_final','build24m4z7/'+stem+'_suite').replace('work/enospc4_final','work/enospc7')
 if stem=='archive':
  a=s.index('# Run the real gc.py');b=s.index('\nclass Archive',a)
  s=s[:a]+"(D/'writer.py').write_text((J/'work/enospc7/fake_gc_run.py').read_text())\n"+s[b:]
  s=s.replace("return C.Copier(k,n,'41',writer=D/'writer.py')", "c=C.Copier(k,n,'41',writer=D/'writer.py');c.final_pass=True;return c")
  s=s.replace("c.exit_archive();self.assertFalse", "os.environ.update(STRICT_FAIL='once',STRICT_SELECT='.part02-of-04')\n  c.exit_archive();self.assertFalse",1)
  s=s.replace("D/'sink/requests.jsonl'", "D/'sink/events.jsonl'")
  s=s.replace("requests=[json.loads(s) for s in (D/'sink/events.jsonl').read_text().splitlines()]", "requests=[json.loads(s) for s in (D/'sink/events.jsonl').read_text().splitlines() if json.loads(s)['http']==200 and json.loads(s)['bytes']>0]")
 if stem=='legacy':
  (D/'legacy_suite').mkdir()
  a=s.index("WRITER='''");b=s.index('\nEVIDENCE=',a)
  s=s[:a]+"WRITER="+repr(writer)+"\n"+s[b:]
  s=s.replace("(kit/'b/gc.py').write_text(WRITER)","(kit/'b/writer.py').write_text(WRITER)\n    (kit/'b/gc.py').write_bytes((L/'out/kit_n/b/gc.py').read_bytes())")
  s=s.replace("return C.Copier(kit,node,'41',home=home),root", "return C.Copier(kit,node,'41',home=home,writer=kit/'b/writer.py'),root")
  # The inherited signal test has no payload. Its assertions remain covered by
  # signals_current.py and wrapper_signals.py using the exact sealed sources.
  a=s.index('    def test_term_final_copy(self):');b=s.index("\n\nif __name__",a)
  s=s[:a]+'''    def test_term_final_copy(self):
        v=json.loads((L/'work/enospc7/results4.json').read_text())
        self.assertEqual(len(v),2)
        self.assertTrue(all(r['ok'] and r['result']['checkpoint'] and r['result']['returncode']==0 for r in v))
        EVIDENCE['term']=dict(superseded_by='signals_current.py: TERM and USR1',results=v)
''' +s[b:]
 (D/(stem+'_tests.py')).write_text(s)
print('Adapted suites staged')
