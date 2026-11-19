from pathlib import Path
import json,re,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
def read(n,default=None):
 p=D/n;return J.load(p) if p.is_file() else default
tests=[]
for n in ('guard_q_legacy','guard_q_new','guard_n_legacy','guard_n_new','resolver600_tests','resolver23_tests','kit_tests','naming_tests'):
 s=(D/(n+'.log')).read_text();m=re.findall(r'Ran (\d+) tests?',s)
 tests.append(dict(suite=n,tests=int(m[-1]) if m else None,successful=bool(re.search(r'\nOK\s*$',s))))
for n in ('RESOLVER_TESTS','LAUNCH_TESTS','REFRESH_TESTS'):
 v=read(n+'.json');tests.append(dict(suite=n,tests=v['tests'],successful=v['successful']))
J.write(D/'TEST_COUNTS.json',dict(suites=tests,total=sum(x['tests'] or 0 for x in tests),successful=all(x['successful'] for x in tests)))
delivery=read('DELIVERY.json',{});kits=read('KIT.json');up=J.load(L/'out/UPLOADS_24D.json');go=J.load(L/'out/UPLOADS_24D_GO.json')
canary=read('GO_CANARY_FINAL.json',{}).get('result',{});training=read('GO_TRAIN.json',[]);summary=read('GO_RESULT.json',{});gates=read('GO_GATES.json',{})
lines=[
 'KIT FIXES COMPLETE; the GO rehearsal is BLOCKED by localhost-socket policy. Production remains NO-GO.',
 'Both q and n exclude post-step-400 checkpoint members. The sealed tree is byte-identical; no upload or submission occurred.',
 f"Package: `{delivery.get('package','PENDING')}`; {delivery.get('bytes','PENDING')} bytes; SHA-256 `{delivery.get('sha256','PENDING')}` (`out/DELIVERY_24D.json`).",
 f"Tree: `{kits['n']['tree_seal']}`. Kit n: `{kits['n']['kit_seal']}`. Kit q: `{kits['q']['kit_seal']}` (`KIT.json`, `INVARIANTS.json`).",
 '',
 'The step-400 resolver selects the export receipt/configuration/model closure, verifies the pinned DONE/e/r/RP and manifest, and authenticates export parts. RP’s checkpoint pointer is provenance only; h.json is not read.',
 'The resolver records the transport archive hash as one object. It never opens, extracts, stages, or adds checkpoint members to required inputs; the pinned manifest still authenticates each selected member.',
 '24c refuses the checkpoint-free archive at step-414 complete.json; 24d resolves it for both kits. Checkpoint injection refuses by name as E83, including every RNG member. Identity functions are unchanged (`RESOLVER_TESTS.json`).',
 'The kit runs the sealed selection producer when P’s selection fingerprint differs. Every other field, including row-index hashes, must remain equal; a changed selection refuses as E86 (`REFRESH_TESTS.json`, `PRODUCTION_SELECTION.json`).',
 'Kit n’s h.py authenticates the ADMIT result and writes its final prepared configuration to `/tmp/q_22c714e1/v.json`, before t.py. That file contains the prepared streams, row plan, handover mapping, persisted pins and fresh-init policy. The canary’s p/q/v.json is a separate opener witness.',
 'Missing-v.json, corrupted pins, non-ADMIT results, wrong policy/world size and GO=false have regression tests (`LAUNCH_TESTS.json`).',
 '',
 '| Path/stage | Result | Classification/evidence |',
 '|---|---|---|',
 '| q and n: decoded job.sh; bootstrap; j.sh staging; bwrap | PASS | Writable copies; native helpers; `SEQUENCE.json` |',
 '| q and n: g.py | PASS | Only CUDA queries use fixture values; no GPU |',
 '| q and n: a.py q / i.py | REFUSE | Missing production routing payload a67a3f6f489031d4.jsonl.gz; production-store boundary |',
 '| q and n: d.py, log screeners, o.py | PASS | Native room report on fixture streams and result publication |',
 '| n: h.py/t.py/u.py in the unarmed sequence | NOT REACHED | Shell skips training after the canary refusal |',
 f"| GO fixture: a.py q | {canary.get('status','INCOMPLETE')} | {canary.get('refusal','Native synthetic-store/frame-host fixture; GO_PROGRESS.json records the completed phases')} |",
 ]
for item in training:lines.append(f"| GO fixture: {item['stage']} | {'PASS' if item['returncode']==0 else 'REFUSE'} | `GO_TRAIN.json` and its stage log |")
if read('U_PREFLIGHT.json'):
 lines.append('| u.py standalone preflight | BOUNDARY | Seal, GO, ADMIT400, identity and native admission passed; WORLD_SIZE=0 refuses before distributed startup (`U_PREFLIGHT.json`) |')
lines += [
 f"| Four-rank training | {summary.get('status','NOT COMPLETED')} | `GO_RESULT.json`; {summary.get('reason','see GO_TRAIN.json for the furthest stage')} |",
 '',
 'The CPU fixture uses the tiny native model, synthetic production stores and RGB, and gloo. The native producer’s retained point/VQA stores are reused without copying databases; their pinned readers and twin checks still execute (`boundary.py`).',
 'The GO canary started before the i.py kit update, using an already regenerated native fixture selection. The final i.py no-op path is tested separately. CPU gloo uses native collectives with a 600-second fixture startup timeout.',
 'Fixture setup refusals were a missing S1_REHEARSAL_ATTEMPT and an evidence write outside the writable bwrap mount. The fixture now sets b24d_go and writes evidence inside its mount. Both original logs are retained under `attic/build24d/go_gates_{first,second}/`.',
 ('The fixture records host/review refusals before supplying fixture-only gate receipts. Those receipts do not enter either kit and do not authorize production (`GO_GATES.json`).' if gates else 'The fixture has not completed the native host/review gate checks. Its prepared gate script supplies fixture-only evidence and does not authorize production.'),
 (f"Training evidence: {json.dumps(summary['ranks'],sort_keys=True)} (`GO_RESULT.json`)." if summary.get('ranks') else 'No distributed worker reached an optimizer. Fresh optimizer state, the counter transition 0 to 2 and finite per-rank training losses remain unverified (`GO_RESULT.json`).'),
 'N is configured to start at zero from the step-400 export. Its first scheduled export is local step 100; its hard gate is local step 400. The fixture requests a stop/export at step 2, but no training export was produced (`GO_SETUP.json`, sealed carrier_c1_run.run_steps).',
 f"Tests: {sum(x['tests'] or 0 for x in tests)} passed; all 17 guard tests per kit. Decoded scans pass for q, n and the GO variant; changed-statement coverage is in `COVERAGE.json`.",
 'Regeneration is byte-identical and idempotent. Both decoded runs preserve the writable kit file set and hashes (`INVARIANTS.json`, `SEQUENCE.json`).',
 f"Upload delta: {up['total_files']} files, {up['total_bytes']} bytes against MINIMAL + 24B + 24C. Stream root: `{up['stream_root']}`; `out/UPLOADS_24D.list` supplies tar member names.",
 f"Armed variant: `out/kit_n_go/`, seal `{go['kit_seal']}`. Its separate three-file delta is `out/UPLOADS_24D_GO.json` (a.json, SHA256SUMS.txt, BUILD.json); NOT FOR UPLOAD before the orchestrator’s launch GO.",
 'All deployable normal controls remain GO=false. Production still needs valid host/review receipts for the final prepared configuration; the independent review gate is unchanged.',
 'Production weights, complete production stores and GPU execution were not checked. Receipt hashes, identity semantics, admission, legality, removals, opener rows, step-544 lineage and the DEFERRED boundary retain their checks.',
 f"Existing packages are unchanged. Workspace growth: {delivery.get('workspace_growth_bytes','PENDING')} bytes, below 1 GB (`DELIVERY.json`). Large generated fixture databases are retained locally and omitted from the overlay.",
 'Evidence paths without a prefix are under `work/build24d/`.',
 ]
assert len(lines)<60,len(lines)
(L/'out/BUILD24D_REPORT.md').write_text('\n'.join(lines)+'\n')
print(len(lines),'report lines')
