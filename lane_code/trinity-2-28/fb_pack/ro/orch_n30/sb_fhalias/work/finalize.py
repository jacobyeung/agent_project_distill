"""Compare focused results and assemble review metadata; archive separately."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];O=W/'out'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={};pairs={}
for group in ('main','edges','producer'):
 pair=[]
 for label in ('before','after'):
  p=O/((f'exact_{label}_main.json') if group=='main' else f'focused_{label}_{group}.json');inputs[str(p)]=sha(p);pair.append(json.loads(p.read_text()))
 b,a=pair
 assert b['successful'] and a['successful'],(group,b['errors'],a['errors'])
 assert b['outcomes']==a['outcomes'],group
 pairs[group]={'before':b['tests'],'after':a['tests'],'differences':[],'errors':0,'failures':0,'blocked_before':b['blocked'],'blocked_after':a['blocked']}
 assert not b['blocked'] and not a['blocked']
assert [pairs[g]['before'] for g in ('main','edges','producer')]==[112,4,11]
host=[]
for label in ('before','after'):
 p=O/f'host_{label}.json';inputs[str(p)]=sha(p);host.append(json.loads(p.read_text()))
assert host[0]['successful'] and host[0]['tests']==1
assert host[1]['tests']==1 and host[1]['errors']==1 and host[1]['failures']==0
for n in ('CHANGED_FILES.json','BOUNDARY_DIFF.json','STATIC_CHECKS.json','boundary_before.json','boundary_after.json'):
 p=O/n;inputs[str(p)]=sha(p)
S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21')
for p in (S/'out/BUILD21H_REPORT.md',S/'work/build21h/HOST_FLAG_BLOCKER.json',Path(__file__).resolve()):inputs[str(p)]=sha(p)
(O/'FOCUSED_DIFF.json').write_text(json.dumps(dict(input_sha256=inputs,suites=pairs,total_per_copy=127,outcome_differences=0,integration_ready=False,additional_host_regression=dict(before=host[0]['outcomes'],after=host[1]['outcomes'])),indent=2)+'\n')
changed=json.loads((O/'CHANGED_FILES.json').read_text())['changed']
lines=[
'Proposal for tree_rebuild13 review; NOT integration-ready. The source lane was not modified. A new tree seal is required.',
'Source: /scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1 (936 files; identical to work/tree_before).',
'ALIAS.patch adds STUDENT_R2_FRAME_HOST → Q_E7 and imports/uses env_key in r2_intake.py and r2_materialize.py.',
'Only the three files below change. Local-node/hostname vetoes, limits, admission predicates and job_env.key stay byte-identical.',
'Native-name fallback is required for P and already exists: key() returns the native name when Q_E7 is absent.',
'launch_r2.host.run_packet sets the native flag; launch_r2.distributed.worker copies K6 to that native flag. Both files stay unchanged.',
'When Q_E7 exists, it takes precedence, including Q_E7=0 over native=1 and Q_E7=1 over native=0.',
'Boundary commands (from this workspace):',
'`bash work/run.sh work/check_boundary.py work/tree_before before` → exit 1, 5 tests, 12 expected subcase failures, 0 errors.',
'`bash work/run.sh work/check_boundary.py work/tree_after after` → exit 0, 5 tests, 0 failures/errors.',
'The three existing empty envelopes are absolute_distance, recovery and units from w21/work/build21/proofs/capacity/400/request_config.json.',
'Q_E7=1 admits all three after and refuses before; missing/zero flags refuse both. Trinity and local-node vetoes refuse both.',
'Native-only 1 passes both; native-only 0 and untranslated K6 refuse both. The worker-translated native flag passes both.',
'The 12 changed subcases cover Q_E7=1 and both conflicting-name cases, across three intake envelopes and materialization.',
'Materialization passes the host boundary then refuses the missing bound sampling table. The local marker and invalid limits still refuse.',
'The real kit environment scanner accepts literal Q_E7=1 and rejects the native-name literal on both copies.',
'Only hostname/environment are substituted for boundary checks; native intake, materializer and scanner functions are unchanged by the harness.',
'Focused main: `bash work/run.sh work/run_focused_exact.py work/tree_LABEL LABEL main`; edges/producer: `bash work/run.sh work/run_focused.py work/tree_LABEL LABEL GROUP` (LABEL=before|after).',
'Focused results per copy: main 112/112, edges 4/4, producer 11/11; all 127 pass with identical outcomes and no blocked operations.',
'`bash work/run.sh work/compare_boundary.py` computes 12 changed subcases; `bash work/run.sh work/finalize.py` compares focused outcomes.',
'`bash work/run.sh work/check_static.py` verifies blocker source hashes and exact preservation of all other lines and P setters.',
'`bash work/run.sh work/seal_patch.py` computes inventories and changed-file SHA-256 values; `patch --dry-run -p1 -d work/tree_before < out/ALIAS.patch` passes.',
'Changed files requiring a new seal (before SHA-256 → after SHA-256):',
]
lines += [f"`{r['path']}`: {r['before']} → {r['after']}" for r in changed]
lines += [
'Additional integration test: `bash work/run.sh work/run_host_regression.py work/tree_LABEL LABEL host` runs test_native_prepare_and_every_rank_encode; before passes, after errors: Statement obligation is ambiguous or absent.',
'launch_r2/runtime.py:62 searches for the old literal lookup. The env_key lookup no longer matches, so run_packet refuses; fixing this requires a separately reviewed fourth-file change, which is NOT in ALIAS.patch.',
'Open risk: inherited Q_E7 overrides P’s native writes; Q_E7=1 prevents its native-zero negative check from refusing at that boundary. Keep Q_E7 absent on legacy P paths.',
'Limits: empty fixtures establish host naming only, not production rows/RGB, full producer success, kit resealing or launch admission. No production launch, GPU, network, SSH, tmux or Git was used.',
'Reproduction needs the read-only w21 fixture paths recorded in evidence JSON input_sha256 maps. Native fixture JSON keeps its required schema; these are test intermediates, not review outputs.',
'The archive contains both trees, patch, report, test harnesses, supporting source files, logs and evidence. `bash work/package.sh` builds it; `sha256sum out/sb_fhalias.tar` gives its sidecar hash.',
'The before/after comparison is retained because the task explicitly requires regression evidence.',
]
lines=[lines[0], '', *('- '+line for line in lines[1:])]
assert len(lines)<=35,len(lines)
(O/'FHALIAS_REPORT.md').write_text('\n'.join(lines)+'\n')
(W/'STATUS.md').write_text('Complete: The exact three-file alias proposal is packaged for tree_rebuild13 review but is NOT integration-ready. Boundary tests fail before and pass after. All 127 focused tests pass on both copies. A separate host integration test passes before and errors after because the patched lookup breaks launch_r2.runtime.obligations. Full inventories confirm that only the intended bytes differ. Native reader fallback remains intact when Q_E7 is absent; inherited Q_E7 precedence is a second compatibility risk. The source lane remains untouched.\n')
print('Report lines',len(lines),'focused tests per copy',127)
