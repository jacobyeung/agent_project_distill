from pathlib import Path
L=Path.cwd();D=L/'work/build24m4q'
s=(L/'work/build24m4p/common.py').read_text().replace("D=L/'work/build24m4p'","D=L/'work/build24m4q'").replace("L/'attic/build24m4p'","L/'attic/build24m4q'")
(D/'common.py').write_text(s)
# Keep inherited data/check assertions; update only intentional publication deltas.
s=(L/'work/build24m4p/publication_tests.py').read_text().replace("D=L/'work/build24m4p'","D=L/'work/build24m4q'")
s=s.replace("L/'attic/build24m4p/out/rcj/x.py'","L/'attic/build24m4q/out/rcj/x.py'")
s=s.replace("z.write(root/'mode.json',dict(mode=mode))","z.write(root/'mode.json',dict(mode=mode))\n        z.write(root/'chain.json',dict(status='PASS',streams={'routing':dict(status='PASS',rows_checked=2,database_rows=2)},population=dict(status='NOT_REACHED')))")
s=s.replace("self.assertEqual(extra,{'routing_types.json'})","self.assertEqual(extra,{'chain.json'})")
s=s.replace("            for key in ('task_a','routing_types','publication_bytes_before_timings','aggregate_publication_bytes','aggregate_limit_status','helper_limit_bytes'):bt.pop(key,None)\n            self.assertEqual(at,bt)", "            bt['task_a'].pop('task_iv');bt['task_a'].pop('population_status')\n            bt.pop('chain')\n            for key in ('publication_bytes_before_timings','aggregate_publication_bytes','aggregate_limit_status','helper_limit_bytes','helper_publication_bytes','helper_limit_status','timings_bytes'):\n                bt.pop(key,None);at.pop(key,None)\n            self.assertEqual(at,bt)")
s=s.replace("dict(status='FAIL',task_i='FAIL',task_ii='PASS',task_iii='PASS'))","dict(status='FAIL',task_i='FAIL',task_ii='PASS',task_iii='PASS',task_iv='PASS',population_status='NOT_REACHED'))")
s=s.replace("patch.object(pc,'selected',return_value=samples),", "patch.object(pc,'metadata_mounts',return_value={}),patch.object(pc,'selected',return_value=samples),")
s=s.replace("'asset':{}}[Path(name).name]", "'asset':{'root':'/project/fixture'}}[Path(name).name]")
s=s.replace("b'\\nRuntimeError: final\\n  note\\n'", "b'\\nTraceback (most recent call last):\\n  File \"x\", line 1\\nRuntimeError: final\\n  note\\n'")
s=s.replace("self.assertEqual({n for n in a if a[n]!=b[n]},{'publish'})", "self.assertEqual({n for n in a if a[n]!=b[n]},{'publish','run_r'})")
s=s.replace("self.assertEqual(set(b)-set(a),{'type_counts'})", "self.assertEqual(set(b)-set(a),{'chain_publish','publication_size'})")
s=s.replace("('rcj.sh','ps.py','P_SAMPLE_I.json','pc.py')", "('rcj.sh','ps.py','P_SAMPLE_I.json')")
s=s.replace("(D/'BASELINE.json').read_bytes()", "(L/'work/build24m4p/BASELINE.json').read_bytes()")
(D/'publication_tests.py').write_text(s)
# Native all-row content/type/absence tests use the real native family function.
s=(L/'work/build24m4p/tests.py').read_text()
s=s.replace("  result=nd.publish_types(p,root/'out/routing_types.json')", "  with patch.object(nd,'native_rules',return_value=None):result=nd.publish_types(p,root/'out/routing_types.json')")
(D/'nd_tests.py').write_text(s)
for name in ('sample','contract'):
 d=D/name;d.mkdir();s=(L/'work/build24m4p'/(name+'_tests.py')).read_text().replace("D=L/'work/build24m4p/", "D=L/'work/build24m4q/")
 (D/(name+'_tests.py')).write_text(s)
 if name=='contract':(d/'rdiff.py').write_bytes((L/'work/build24m4p/contract/rdiff.py').read_bytes())
