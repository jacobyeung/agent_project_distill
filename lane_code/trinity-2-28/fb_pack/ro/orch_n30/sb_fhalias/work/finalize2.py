"""Validate CPU evidence and produce the integration report and input hashes."""
from pathlib import Path
import hashlib
import json
W=Path(__file__).resolve().parents[1]
O=W/'out'
inputs={}
def read(name):
 p=W/name;raw=p.read_bytes();inputs[str(p)]=hashlib.sha256(raw).hexdigest()
 return json.loads(raw) if p.suffix=='.json' else raw.decode()
pairs={}
for group in ('main','edges','producer'):
 results=[]
 for label in ('before','after'):
  stem=f'exact_{label}2_main' if group=='main' else f'focused_{label}2_{group}'
  result=read('out/'+stem+'.json');read('out/'+stem+'.log')
  assert result['successful'] and not result['blocked'] and not result['skipped'],stem
  results.append(result)
 assert results[0]['outcomes']==results[1]['outcomes'],group
 pairs[group]=dict(before=results[0]['tests'],after=results[1]['tests'],differences=[])
assert [pairs[g]['before'] for g in pairs]==[112,4,11]
host={}
for label,stem in [('before','host_before2_final'),('after','host_after2_final'),('before_checks','host_before2_final_checks'),('after_checks','host_after2_checks')]:
 result=read('out/'+stem+'.json');read('out/'+stem+'.log')
 assert result['successful'] and not result['blocked'] and not result['skipped'],stem
 assert result['tests']==(12 if label.endswith('checks') else 1),(label,result['tests'])
 host[label]=dict(tests=result['tests'],outcomes=result['outcomes'])
for label in ('before','after'):
 result=read(f'out/boundary_{label}2_contract.json');read(f'out/boundary_{label}2_contract.log')
 assert result['successful'] and result['tests']==5
mutations={}
for label in ('before','after'):
 result=read(f'out/missing_intake_{label}2.json');read(f'out/missing_intake_{label}2.log')
 assert result['successful'] and result['refused']==(label=='after')
 mutations[label]=result['refused']
bound=read('out/BOUNDARY_DIFF2.json');assert bound['changed_count']==12
checks=read('out/STATIC_CHECKS2.json');assert all(checks['checks'].values())
changes=read('out/CHANGED_FILES.json');assert len(changes['changed'])==6 and changes['source_matches_before']
read('out/ALIAS.patch');read('out/patch_dry_run2.log')
for name in ('source_matches.txt','nonpython_matches.txt','source_pattern_audit.txt','source_text_consumers.txt'):
 read('out/'+name)
for name in ('run.sh','run_focused.py','run_focused_exact.py','run_host_regression.py','alias2_tests.py','check_missing_intake_tree.py','check_boundary2.py','check_static2.py','seal_patch2.py','compare_boundary2.py','finalize2.py'):
 read('work/'+name)
result=dict(input_sha256=inputs,integration_ready_for_review=True,requires_new_tree_seal=True,
 focused=pairs,total_focused_per_copy=127,host=host,missing_intake_tree_refused=mutations,boundary_tests_per_copy=5,boundary_changed_subcases=12,
 baseline_intake_source_check='absent; mutation is accepted before and refused after',
 limits=['CPU synthetic host regression; no production launch or full population evidence',
        'Host full-store native mutation is tested using actual AST statements and real materializer, without production setup',
        'Worker translation stops before source verification and training',
        'Five execution receipts retained; intake check is a source precondition, not an execution receipt'])
(O/'FHALIAS2_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
lines=[
'Integration-ready for review: six-file patch; 127 focused tests and the host regression pass on both copies. A new tree seal is required.',
'`student_pilot/job_env.py:4`: adds Q_E7; `key()` is unchanged. Boundary tests cover native fallback and alias precedence.',
'`student_pilot/r2_intake.py:10,39` and `r2_materialize.py:5,26`: resolve the host flag through env_key; boundary tests preserve limits and local/Trinity vetoes.',
'`launch_r2/runtime.py:61–66`: matches the exact env_key lookup and requires exactly one intake guard; five execution receipts remain unchanged in shape.',
'Runtime mutations remove or duplicate each guard: materializer refuses on both copies; intake refuses after. `bash work/run.sh work/check_missing_intake_tree.py work/tree_LABEL LABEL2` verifies an actual mutated tree (accepted before, refused after).',
'`launch_r2/host.py:253`: clears inherited Q_E7 before checks/scene preparation, preserving native zero/one writes; host regressions test inherited 0 and 1.',
'`launch_r2/distributed.py:77`: clears Q_E7 before K6 translation; 27 environment combinations preserve legacy native behavior, including absent K6.',
'`rg -n -m 12 "STUDENT_R2_FRAME_HOST|Q_E7|Statement obligation|getsourcelines|inspect.getsource" work/tree_before -g "*.py"` locates consumers; source_matches.txt records them. No other frame-host text matcher exists.',
'Commands below run from this workspace through run.sh (nice 10, eight CPU threads, offline, CUDA hidden). LABEL means before or after.',
'`bash work/run.sh work/check_boundary2.py work/tree_LABEL LABEL2_contract`: 5/5 pass per copy; expectations encode each copy’s contract.',
'`bash work/run.sh work/compare_boundary2.py`: 12 changed subcases across intake/materialization; scanner admits Q_E7 and rejects the native-name literal on both.',
'`bash work/run.sh work/run_focused_exact.py work/tree_LABEL LABEL2 main`: 112/112 each; `bash work/run.sh work/run_focused.py work/tree_LABEL LABEL2 GROUP`: edges 4/4 and producer 11/11 each.',
'`bash work/run.sh work/run_host_regression.py work/tree_LABEL LABEL2_final host`: 1/1 each; test_native_prepare_and_every_rank_encode passes.',
'`bash work/run.sh work/run_host_regression.py work/tree_before before2_final_checks integration` and `... work/tree_after after2_checks integration`: 12/12 each, including runtime containment and source mutations.',
'Full-host mutation tests execute the actual host AST statements with the real materializer; worker tests stop before source verification/training. These tests do not admit production.',
'`bash work/run.sh work/check_static2.py`: only intended lines change; `bash work/run.sh work/seal_patch2.py`: 936-file inventories, source==before, six changed files and SHA-256 values below.',
'`patch --dry-run -p1 -d work/tree_before < out/ALIAS.patch` passes. `bash work/run.sh work/finalize2.py` verifies counts and matching focused outcomes.',
]
lines += [f"`{r['path']}`: {r['before']} -> {r['after']}" for r in changes['changed']]
lines += [
'Remaining risks: exact source-text checks retain formatting sensitivity; intake validation does not add an execution receipt. Legacy P paths intentionally ignore inherited Q_E7.',
'Empty envelopes/synthetic RGB establish boundaries and CPU encoding only; production data, full producer success, kit resealing and launch admission remain unverified.',
'Reproduction uses existing w21 fixtures listed by exact path/hash in evidence JSON. Native fixture JSON retains its schema; all review JSON records input_sha256.',
'`bash work/package2.sh` creates out/sb_fhalias2.tar and its SHA-256 sidecar; `bash work/run.sh work/verify_archive2.py` verifies archived bytes, hashes and report length.',
'The source lane is read-only and unchanged. No GPU, network, SSH, tmux, Git, process termination or deletion was used.',
]
assert len(lines)<=30,len(lines)
(O/'FHALIAS2_REPORT.md').write_text('\n'.join(lines)+'\n')
(W/'STATUS.md').write_text('Validation complete: all 127 focused tests, the host regression, five boundary-contract tests, and twelve integration tests pass on each copy. Source mutations confirm fail-closed materializer checks on both copies and intake checks after the patch. Six intended files change; the baseline remains identical to the source lane. The regenerated patch applies cleanly. Archive creation and verification are pending.\n')
print('PASS: report',len(lines),'lines; 127 focused + 1 host + 12 integration + 5 boundary tests per copy')
