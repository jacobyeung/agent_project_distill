from common import *
scripts=('checks','run_suites','kit_tests','naming_tests','resolver_tests','resolver600_tests','resolver23_tests','live_tests','review_tests','security_tests','guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','publication_tests','regression_tests','tiny_routing','p_refresh_tests','native_host_tests','planner_all','source_pin_tests','discovery_shell','run_extra')
for n in scripts:
 s=(L/'work/build24m2d'/(n+'.py')).read_text().replace('work/build24m2d','work/build24m3')
 if n=='kit_tests':
  s=s.replace("paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m2c'/('UPLOADS_'+name+'.json'))['files']}","paths={x['sha256']:x['local_path'] for x in J.load(L/'work/build24m2c'/('UPLOADS_'+name+'.json'))['files']};paths.update({p.name:str(p) for p in (L/'work/build24m3/u').iterdir()})")
  s=s.replace("self.assertEqual([v['sha256'] for v in c['remove_files']],[v['sha256'] for v in before['remove_files']]);self.assertEqual(len(c['remove_files']),12)","self.assertEqual([v['sha256'] for v in c['remove_files'] if v.get('role')!='protected_rooms'],[v['sha256'] for v in before['remove_files']]);self.assertEqual(len(c['remove_files']),13)")
 (D/(n+'.py')).write_text(s)
for n in ('live.py','live.sh'):(D/n).write_bytes((L/'work/build24m2d'/n).read_bytes())
# Native tests retain temporary fixtures; never use unittest cleanup deletion.
s=(D/'native_host_tests.py').read_text().replace('test_host24j,test_host24l,test_host24n,test_host24l3','test_host24j,test_host24l,test_host24n,test_host24l3,test_host24l4r')
replace(D/'native_host_tests.py',s)
# Legacy scan controls are retained unchanged except current source seals.
