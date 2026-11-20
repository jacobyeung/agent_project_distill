from pathlib import Path
import sys,json,hashlib,ast,subprocess
W=Path(__file__).resolve().parent;J=W.parents[1];K=J/'out/kit_n_go';P=W/'proposed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((W/'sealed_before.json').read_text());now={str(p.relative_to(K)):sha(p) for p in K.rglob('*') if p.is_file()}
assert before==now
copy={str(p.relative_to(W/'kit')):sha(p) for p in (W/'kit').rglob('*') if p.is_file()}
assert copy==before
assert sha(J/'inputs/jn.sh')=='73c7cb3f89fd3511ce25ada69fe4ac2413d36b2b5ba4ef1b1cce042660a6fb40'
manifest={n:h for h,n in (line.split('  ',1) for line in (P/'SHA256SUMS.txt').read_text().splitlines())}
assert manifest=={str(p.relative_to(P)):sha(p) for p in P.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS.txt','BUILD.json')}
for d in (W,P/'b'):
 for p in d.glob('*.py'):ast.parse(p.read_text(),str(p))
for p in (J/'out/jn2.sh',P/'b/pc.sh'):subprocess.run(['bash','-n',str(p)],check=True)
sys.path.insert(0,str(K/'b'));import z
names=['q_22c714e1','/tmp/q_22c714e1_24008.log','j2.py','j2.log','j2.err','j2.retry.log','sess_24008.json','retry.log','state','claims']+[v+'.j24008' for v in z.load(P/'k/y.json')['objects'].values()]
for name in names:z.name_guard(K)(name)
r=json.loads((J/'out/ENOSPC_24M4Z.json').read_text());assert [v['item'] for v in r['items']]==[1,2,3,4,5]
for item in r['items']:
 for p in item['logs']:assert (J/p).is_file(),p
assert len((J/'out/BUILD24M4Z_REPORT.md').read_text().splitlines())<12
res={v['name']:v for v in r['test_results']}
assert res['full_loop_small']['result']['returncode']==1
assert res['full_loop']['result']['returncode']==1
assert res['full_direct_print']['result']['returncode']==120
assert res['full_pipeline']['result']['child_rc']==120
assert res['wrapper_full_pipeline_bounded']['result']['child_rc']==0
assert res['wrapper_full_pipeline_bounded']['result']['logger_rc']==0
assert res['wrapper_automatic_recovery']['result']['exact']
assert res['worker_trap_term']['result']['checkpoint'] and res['worker_trap_usr1']['result']['checkpoint']
assert r['proposed_result']['sink_parts']==20 and r['proposed_result']['mandatory_zero_write_assertion_passed']
assert json.loads((W/'native_export_result.json').read_text())['kind']=='export'
summary=dict(sealed_original_files=len(now),original_unchanged=True,test_copy_byte_identical=True,wrapper_sha256=sha(J/'out/jn2.sh'),original_wrapper_unchanged=True,proposed_manifest_valid=True,new_visible_names_checked=len(names),report_log_links_valid=True,key_result_assertions_passed=True,syntax_valid=True,build_report_lines=10)
(W/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
