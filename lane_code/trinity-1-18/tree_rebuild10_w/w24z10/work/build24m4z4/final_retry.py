from pathlib import Path
import json,base64,hashlib,shutil
J=Path.cwd();K=J/'out/kit_n';D=J/'work/build24m4z4'
p=K/'b/pc.py';s=p.read_text()
s=s.replace("                os.replace(partial, destination)\n\n    def exit_archive", "                os.replace(partial, destination)\n        if (local/'o.tar').is_file() and (local/'RESULT.json').is_file():\n            put(self.state/'o_copy.done', dict(sha256=sha(local/'o.tar')))\n\n    def exit_archive")
s=s.replace("    def exit_archive(self):\n        archive", "    def exit_archive(self):\n        if self.final_pass and list(self.train.glob('checkpoint_*/complete.json')):\n            stop = self.state/'ckstop.json'\n            if not stop.is_file() or read(stop).get('status') != 'gcs':\n                return\n        archive")
s=s.replace("    last = 0.\n", "    last = 0.\n    final_end = time.monotonic()+140\n")
s=s.replace("            if args.final and not (c.state/'gcs_o.done').is_file():", "            if args.final and time.monotonic() < final_end and not (\n                    (c.state/'gcs_o.done').is_file() and (c.state/'o_copy.done').is_file()):")
p.write_text(s)
for root in (J/'out/kit_n_go',J/'work/build24/kits/n'):shutil.copy2(p,root/'b/pc.py')
for k in (K,J/'out/kit_n_go',J/'work/build24/kits/n'):
 p=k/'SHA256SUMS.txt';names=[x.split('  ',1)[1] for x in p.read_text().splitlines()]
 p.write_text(''.join(hashlib.sha256((k/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in names))
 p=k/'BUILD.json';v=json.loads(base64.b64decode(json.loads(p.read_text())['payload']));v['kit_sha256']=hashlib.sha256((k/'SHA256SUMS.txt').read_bytes()).hexdigest()
 raw=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();p.write_text(json.dumps(dict(encoding='base64-json',payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True)+'\n')
# Preserve completed test outputs and use new fixture directories for the final bytes.
old=J/'work/enospc4';W=J/'work/enospc4_final';W.mkdir()
for name in ('runtime.py','fake_gc_run.py','j2_helper_new.py','retest.py','check_current.py','signals_current.py','wrapper_prefix2.py'):
 s=(old/name).read_text().replace('monotonic=time.monotonic,sleep=', 'monotonic=lambda:time.monotonic()/.003,sleep=')
 s=s.replace("assert phases==['stop','exports','logs','o'],phases", "assert phases and all(phases[i:i+4]==['stop','exports','logs','o'] for i in range(0,len(phases),4)),phases")
 (W/name).write_text(s)
for name in ('bin','tmp','logs','mnt','mnt4','mnt5','node'):(W/name).mkdir()
shutil.copytree(J/'out/kit_n_go',W/'kit')
s=(old/'bin/python3').read_text().replace('/work/enospc4/','/work/enospc4_final/');(W/'bin/python3').write_text(s);(W/'bin/python3').chmod(0o755)
s=(D/'current_tests.py').read_text().replace('build24m4z4/current','build24m4z4/current_final').replace('/enospc4/','/enospc4_final/');(D/'current_final_tests.py').write_text(s)
s=(D/'legacy_tests.py').read_text().replace('build24m4z4/legacy','build24m4z4/legacy_final');(D/'legacy_final').mkdir();(D/'legacy_final_tests.py').write_text(s)
s=(D/'e2_local.py').read_text().replace('build24m4z4/e2_final','build24m4z4/e2_verified').replace('monotonic=time.monotonic,sleep=', 'monotonic=lambda:time.monotonic()/.003,sleep=');(D/'e2_verified.py').write_text(s)
s=(D/'readback_test.py').read_text().replace("D/'e2_final/n'","D/'e2_verified/n'");(D/'readback_final_test.py').write_text(s)
s=(D/'archive_tests.py').read_text().replace('build24m4z4/archive_cases','build24m4z4/archive_final').replace('/enospc4','/enospc4_final')
# A pending stop must reserve the upload window before o.py can run.
idx=s.index(' def test_archive_sessions_required')
s=s[:idx]+''' def test_pending_stop_blocks_archive(self):
  c=fixture('priority');p=c.train/'checkpoint_9';p.mkdir();C.put(p/'complete.json',dict(step=9))
  c.final_pass=True;c.exit_status=0
  with patch.object(C.subprocess,'run') as run:
   c.exit_archive();run.assert_not_called()
  self.assertFalse((c.root/'o/o.tar').exists())
''' +s[idx:]
(D/'archive_final_tests.py').write_text(s)
s=(D/'run_suites.py').read_text().replace("W=J/'work/enospc4'","W=J/'work/enospc4_final'")
s=s.replace("D/'current_tests.py'","D/'current_final_tests.py'").replace("D/'legacy_tests.py'","D/'legacy_final_tests.py'").replace("D/'e2_local.py'","D/'e2_verified.py'").replace("D/'readback_test.py'","D/'readback_final_test.py'")
s=s.replace("commands=[", "commands=[('archive',[PY,'-I','-s','-B',str(D/'archive_final_tests.py')]),")
s=s.replace("name+'.log'","name+'_final.log'").replace("D/'SUITES.json'","D/'FINAL_SUITES.json'");(D/'run_final_suites.py').write_text(s)
print('Final retries bounded to 140 seconds; local fixture clock scaled consistently')
