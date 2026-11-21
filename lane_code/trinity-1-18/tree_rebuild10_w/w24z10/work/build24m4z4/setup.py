from pathlib import Path
import shutil,json,sys,hashlib,tarfile,os
J=Path.cwd();D=J/'work/build24m4z4';W=J/'work/enospc4';W.mkdir()
old=J/'work/enospc2'
for name in ('runtime.py','fake_gc_run.py','j2_helper_new.py','retest.py','check_current.py','signals_current.py','wrapper_prefix2.py'):
 s=(old/name).read_text();(W/name).write_text(s)
for name in ('bin','tmp','logs','mnt','mnt4','mnt5','node'):(W/name).mkdir()
shutil.copytree(J/'out/kit_n_go',W/'kit')
s=(W/'runtime.py').read_text().replace("   a=list(a);a[a.index(str(K/'b/gc.py'))]=str(W/'fake_gc_run.py')","   a=list(a);a[a.index(str(K/'b/gc.py'))]=str(W/'fake_gc_run.py')\n  elif isinstance(a,list) and str(K/'b/o.py') in a:\n   i=a.index(str(K/'b/o.py'));a=a[:i]+[str(W/'runtime.py')]+a[i:]")
(W/'runtime.py').write_text(s)
(W/'bin/python3').write_text('#!/bin/bash\nexec '+sys.executable+' -I -s -B '+str(W/'runtime.py')+' "$@"\n');(W/'bin/python3').chmod(0o755)
s=(W/'retest.py').read_text().replace("archive_retry=(N/'o/retry.log').read_text()","archive_retry=(N/'live_spool/retry.log').read_text()")
s=s.replace("'gcs_m100.done'],done","'gcs_m100.done','gcs_o.done'],done").replace('len(receipts)==12','len(receipts)==16').replace('len(sink)==12','len(sink)==16')
s=s.replace(" raise AssertionError('No exit-archive GCS object or upload route in adopted patch; o.tar remains node-local while X is full')",''' assert shutil.disk_usage(X).free==0
 receipt=json.loads((N/'live_spool/state/gcs_o.done').read_text())
 rows=[json.loads(s) for s in (N/'live_spool/private/sess.json.receipts.jsonl').read_text().splitlines()]
 rows=sorted((r for r in rows if r['name'].startswith(receipt['object']+'.part')),key=lambda r:r['offset'])
 raw=b''
 for i,row in enumerate(rows):
  # The local sink hashes the request path, including gc.py's trailing question mark.
  path='/o/'+str(i)+'?'
  raw+=(W/'sink'/hashlib.sha256(path.encode()).hexdigest()).read_bytes()
 assert len(rows)==4 and raw==(N/'o/o.tar').read_bytes()
 assert hashlib.sha256(raw).hexdigest()==receipt['sha256'] and len(raw)==receipt['bytes']
 import io,tarfile
 with tarfile.open(fileobj=io.BytesIO(raw)) as t:assert json.load(t.extractfile('RESULT.json'))['proof_rc']==0
 phases=[json.loads(s)['phase'] for s in (N/'live_spool/final_order.jsonl').read_text().splitlines()]
 assert phases==['stop','exports','logs','o'],phases
 return dict(project_free=0,bytes=len(raw),sha256=receipt['sha256'],parts=4,RESULT_inside=True,final_order=phases)''')
s += "\nassert all(r['status']=='PASS' for r in results),results\n"
(W/'retest.py').write_text(s)
s=(W/'signals_current.py').read_text().replace("os.environ.update(TEST_X=", "os.environ.update(FAKE_SINK=str(W/'sink4'),TEST_X=")
# Each signal case is its own allocation-local archive; retain the inherited worker assertions.
(W/'signals_current.py').write_text(s)
s=(J/'work/build24m4z2/current_tests.py').read_text().replace('build24m4z2/current','build24m4z4/current').replace('work/enospc2/fake_gc_run.py','work/enospc4/fake_gc_run.py')
(D/'current_tests.py').write_text(s)
s=(J/'work/build24m4z2/legacy_ready_tests.py').read_text().replace('/w24z2','/w24z4').replace('build24m4z2/legacy_ready','build24m4z4/legacy')
s=s.replace("('m100','mstop','mstopB','mstopC','ckstop')","('m100','mstop','mstopB','mstopC','ckstop','o',*('ck%02d'%i for i in range(16)))")
s=s.replace("    return C.Copier(kit,node,'41',home=home),root","    (home/'sess_41.json').write_bytes((home/'sess.json').read_bytes());(home/'sess_41.json').chmod(0o600)\n    # The launch finalizer uses these unchanged helpers with the new four-file kit.\n    for name in ('o.py','z.py','wh.json','ep.py'):\n        (kit/'b'/name).write_bytes((L/'out/kit_n_go/b'/name).read_bytes())\n    for name in ('g.json','r.json'):\n        (kit/'k'/name).write_bytes((L/'out/kit_n_go/k'/name).read_bytes())\n    return C.Copier(kit,node,'41',home=home),root")
s=s.replace("        c.exports();self.assertEqual(C.read(c.live/'gcs_m100.json')['status'],'export not uploaded: sessions unusable (file missing)')\n        self.assertEqual(len(list(c.spool.glob('*.tar'))),1)","        cached=c.spool/'private/sess.json';cached.rename(c.spool/'private/held.json')\n        (c.home/'sess.json').rename(c.home/'held.json')\n        with self.assertRaisesRegex(ValueError,'file missing'):C.Copier(c.kit,c.root,'41',home=c.home)\n        (c.home/'held.json').rename(c.home/'sess.json');(c.spool/'private/held.json').rename(cached)")
s=s.replace("c.live/'gcs_","c.state/'gcs_").replace("c.live.glob('gcs_","c.state.glob('gcs_").replace("c.live/'ckstop.json'","c.state/'ckstop.json'")
start=s.index('        c,root=fixture(\'checkpoint_project\')');end=s.index('\n    def test_term_final_copy',start)
s=s[:start]+'''        c,root=fixture('checkpoint_project');state(c,'checkpoint_000001');last=state(c,'checkpoint_000003')
        with patch.object(C.shutil,'disk_usage',return_value=SimpleNamespace(free=100*1024**3)):c.stop_checkpoint()
        v=C.read(c.state/'ckstop.json');self.assertEqual(v['status'],'gcs');self.assertEqual(v['marker_sha256'],C.sha(last))
        self.assertFalse((c.target/'n_ck/41').exists())
        EVIDENCE['checkpoint_ample']=v
        c,root=fixture('checkpoint_gcs');state(c,'checkpoint_000003')
        usage=lambda p:SimpleNamespace(free=0 if Path(p)==c.target else 100*1024**3)
        with patch.object(C.shutil,'disk_usage',side_effect=usage):c.stop_checkpoint()
        self.assertEqual(C.read(c.state/'ckstop.json')['status'],'gcs')
        EVIDENCE['checkpoint_full']=C.read(c.state/'gcs_checkpoint_000003_stop.done')
        c,root=fixture('checkpoint_local_full');state(c,'checkpoint_000003')
        with patch.object(C.shutil,'disk_usage',return_value=SimpleNamespace(free=0)):
            with self.assertRaisesRegex(ValueError,'E95'):c.stop_checkpoint()
        self.assertFalse((c.state/'gcs_checkpoint_000003_stop.done').exists())
''' +s[end:]
s=s.replace("unittest.TestSuite(Live24F(n) for n in ['test_byte_cap_and_marker_only_listing','test_term_final_copy'])","unittest.defaultTestLoader.loadTestsFromTestCase(Live24F)")
(D/'legacy').mkdir();(D/'legacy_tests.py').write_text(s)
# Every driver uses its own fresh fixture and the new kit bytes.
s=(J/'work/build24m4z2/e2_final.py').read_text().replace('build24m4z2/e2_final','build24m4z4/e2_final')
s=s.replace("report['status']=='FAIL' and report['checks']['archive_while_full']=='FAIL'","report['status']=='PASS' and report['checks']['archive_while_full']=='PASS'")
s=s.replace('==12','==16').replace('objects=12','objects=16')
(D/'e2_local.py').write_text(s)
s=(J/'work/build24m4z2/readback_test.py').read_text().replace('build24m4z2','build24m4z4').replace('len(calls)==25','len(calls)==33').replace('objects=12','objects=16').replace('serial_requests=24','serial_requests=32').replace('12 objects','16 objects')
(D/'readback_test.py').write_text(s)
s=(J/'work/build24m4z2/verify_delta.py').read_text().replace('build24m4z2','build24m4z4');(D/'verify_delta.py').write_text(s)
print('Harnesses ready')
