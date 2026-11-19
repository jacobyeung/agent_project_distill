"""Source-linked handoff; missing proofs remain explicit blockers."""
import collections
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
def read(name):return json.loads((L/name).read_text())
def line(name,needle):
    for number,text in enumerate((L/'work/tree_r1'/name).read_text().splitlines(),1):
        if needle in text:return 'work/tree_r1/'+name+':'+str(number)
    return 'work/tree_r1/'+name
row_results='work/build4/rows_final_source/RESULTS.json' if (L/'work/build4/rows_final_source/RESULTS.json').exists() else 'work/build4/rows_complete/RESULTS.json'
rows=read(row_results)
coverage=read('work/build4/CHANGED_COVERAGE.json') if (L/'work/build4/CHANGED_COVERAGE.json').exists() else None
packages=[]
for p in sorted((L/'work/build4').glob('package_*/PACKAGE_RESULT.json')):
    packages.append((str(p.relative_to(L)),json.loads(p.read_text())))
mutation=read('work/build4/mutation_final/RESULTS.json')
seal=read('out/TREE_SEAL.json')
kit_results=read('work/build4/kits/RESULTS.json')
proof=row_results
table=['| Slice / family | Seen | Admitted | Refused | eval_rooms | Production repeats | Evidence |',
       '|---|---:|---:|---:|---:|---|---|']
for r in rows:
    table.append('| '+r['group']+'/'+r['family']+' | '+str(r['seen'])+' | '+str(r['admitted'])+' | '+str(r['refused'])+' | '+str(r['eval_rooms'])+' | unqualified: slice only | `'+r['report']+'` |')
repeat='\n'.join(table)
(L/'out/BUILD4_REPEAT_TABLE.md').write_text('# Filtered slice denominators\n\nEvery count below comes from its row’s evidence path. Production repeats require the complete filtered population; bounded slices cannot establish them. `eval_rooms` remains active for every VQA family.\n\n'+repeat+'\n')
fixes=[
 ('1','PARTIAL',line('launch_r2/staging.py','def main('),'Pinned runtime and sandbox command implemented; production verification runs before staging. Actual venv/bwrap bytes are absent from named inputs, so neither Python-without-numpy entry proof nor Python 3.6 execution is established. Syntax-only evidence: `work/build4/KIT_CHECKS.json`.'),
 ('2','PARTIAL',line('launch_r2/plan.py','def make('),'Every relative config path has a staging entry, and the walker refuses gaps. Tiny assembly/hash/escape tests pass. Actual parent archives and nested native path layout remain unverified; a staging-list entry is not a physical staging proof. `work/build4/KIT_CHECKS.json`; `tests.test_r2_build4`.'),
 ('3','PARTIAL',line('student_pilot/r2_adapters.py','def normalize('),'Published nested questions, ground_record events and raw printed pool events use the masked reader; the envelope pins the shared contract. Recovery prose, converted units and sealed simulated misses pass. Per-row refusals retain denominators. Required slice results are below. Full-store final sampler reindexing after a late frame/materialization refusal remains unproved.'),
 ('4','PARTIAL',line('launch_r2/persistence.py','def upload('),'Milestone/checkpoint callbacks archive and verify locally, upload through the pinned parent writer, then permit project mirroring. Signal handler requests stop through a local file. The fake uploader proves archive/range receipts survive project ENOSPC. Retained checkpoint archive copies are not yet folded into the native whole-leg disk budget. Real checkpoint restore, remote sessions, deadline/memory admission and durable manifest recovery remain unqualified. `work/build4/tests_quick_final/PERSISTENCE.json`.'),
 ('5','FIXED; DELIVERY BLOCKED',line('student_pilot/r2_policy.py','def read_bank('),'Gateway requires a verified kit; file/item membership and choices come from its bound config. Reviewer relabel/omitted-selector probes refuse. Delivered catalog is empty because real bank bytes were not supplied; no evaluation is admitted. `work/build4/review_current/PROBE_BANK.json`; `tests.test_r2_policy`.'),
 ('6','FIXED',line('student_pilot/r2_contract.py','def event_row('),'GT mask and geometry provenance are mandatory; selector authority refuses. Published-row mutations refuse. `work/build4/review_current/MUTATIONS.json`; `tests.test_r2_build4`.'),
 ('7','FIXED',line('launch_r2/parent.py','def reproduce('),'Real parent records pass through configure(overrides=False); garbage parents refuse. Parent metadata is in fixtures. `tests.test_r2_build4.ReviewGuards.test_parent_configuration_path`; `tests.test_r2_build3`.'),
 ('8','FIXED',line('student_pilot/r2_scene_bindings.py','def require_merged('),'Merged bytes bind config, totals, census and pool upstream. Prior derivation is only an equivalence test. `tests.test_r2_build3b`; `student_pilot/r2_dev_merged.json` has the requested digest.'),
 ('9','PARTIAL',line('student_pilot/r2_openers.py','def preparation('),'Keep now refuses missing witness, wrong lineage or non-full LM at preparation, and never resets silently. Actual vocabulary witness remains absent; delivered config explicitly binds null and cannot prepare. `tests.test_r2_build4`; `tests.test_r2_build3`.'),
 ('10','FIXED',line('launch_r2/bootstrap.py','a.main(root, build_only=False)'),'Both production bootstrap levels invoke native ANON_OK/status/hits/commit checks. Builder verification alone retains build-only mode. `work/build4/KIT_CHECKS.json`; `tests.test_r2_build`.'),
 ('11','PARTIAL',line('launch_r2/build.py','def scan('),'Metadata/disclosure capsules, local source extraction, opaque shell variables and hashed refusal/log records are implemented. Scanner covers output paths, all JSON-looking files and every uncapsulated field, with no output-path exceptions. Both staged kits scan clean. Native runtime output surfaces after full host execution remain unqualified.'),
 ('12','FIXED',line('launch_r2/build.py','authorization = dict('),'Each kit carries its own unsigned GO=false authorization and bound config digest. No parent conditions authorize this leg. `work/build4/KIT_CHECKS.json`.'),
 ('13','FIXED',line('launch_r2/host.py','Packet configuration differs'),'Host checks packet/config bytes against the kit; entry checks the bound original and prepared config digest. Derived store-path changes are separately hashed. `tests.test_r2_build3_gaps`.'),
 ('14','FIXED',line('student_pilot/r2_exclusions.py',"self.names['eval_rooms']"),'Conservative eval_rooms exclusion remains active for every VQA family. Card and repeat table list its observed slice removals. Production repeats remain unqualified. `out/BUILD4_REPEAT_TABLE.md`.'),
 ('15','FIXED',line('student_pilot/r2_materialize.py','Duplicate QID across families'),'Refusal names both families and keeps the rejected row in its denominator. `tests.test_r2_data_path`.'),
 ('16','FIXED',line('student_pilot/carrier_c1_data.py','def mixed_indices('),'R2 training and host reader paths require bound sampling; natural-draw fallback refuses. `tests.test_r2_build4.ReviewGuards.test_missing_sampler_refuses`; `tests.test_r2_sampling`.'),
 ('17','FIXED FOR REVIEW MUTATIONS',line('tests/test_r2_build4.py','class ReviewGuards'),'All applicable reviewer statement mutations are killed; removed per-row contract mutation is replaced by envelope/version tests. The mutation harness changes live function code while retaining source pins; each targeted baseline passes. `work/build4/mutation_final/RESULTS.json`; final grammar recheck: `work/build4/mutation_current_grammar/RESULTS.json`.')]
parts=['# Build 4 report','', '**NOT READY.** The tree and kits contain tested intake and admission repairs, but the exact runtime staging proof, durable full-state recovery qualification, vocabulary witness, complete package pass and zero-gap CPU coverage are not established. No launch, remote call or GPU work was performed.', '',
 'The disposition identifiers below refer to `work/review1/REVIEW_VERDICT_TREE.md` and the build request. “FIXED” describes the named behavior, not production readiness.', '',
 '| Review item | Disposition | Implementation | Evidence / remaining work |','|---|---|---|---|']
parts += ['| '+' | '.join(v)+' |' for v in fixes]
parts += ['', '## Real rows and causes', '',
 'The unchanged published slices run through the real normalizer, validator, intake and materializer to the frame-host marker. RGB paths/hashes stand in; no real RGB is read. Coverage envelopes copy published scene identities and do not establish a new independent scene census. Missing source-length fields use the explicit lower bound max(source ordinals)+1 only in this metadata proof. FPS joins use the parent authority and published row metadata, never answers; every join source is recorded in `work/build4/rows_complete/CLOCKS.json`. Source rows remain unchanged. The initial command was `work/build1/REAL_ROW_PROOF.sh work/build4/rows_complete`; `work/build4/replay_materialize.py` reuses its immutable envelopes for the final shared-grammar wrapper.', '',repeat,'',
 'Every refusal is listed by QID in its materialization report. Non-exclusion causes:', '']
for r in rows:
    reasons={k:v for k,v in r['reasons'].items() if not k.startswith('excluded:')}
    if reasons:parts.append('- `'+r['group']+'/'+r['family']+'`: '+ '; '.join(str(v)+' × `'+k+'`' for k,v in reasons.items())+'. Source: `'+r['report']+'`.')
parts += ['', 'These causes are not waived: the shared grammar rejects unsupported quantities, exhaustive frame assertions and missing reasoning; direct-only rows cannot enter the event path; raw room rows lack required source/frame lineage; clock joins refuse missing or contradictory evidence. Older pool rows retain their original wording. Contract patches remain out of scope.', '',
 '## CPU proofs and package', '',
 'The native producer/reader proofs use synthetic RGB and TinyProcessor at the pretrained input interface. The separate model proof runs native forward/backward with tiny random weights and synthetic vision tensors. These are explicit stand-ins, not a proof with the real pretrained RGB processor, towers or export. Sources: `work/build4/tests_current/B3_NATIVE_JOB_PROOF.json`, `B3B_NATIVE_PROOF.json`, `B2_MODEL_PROOF.json` and the associated test files.', '',
 'Temporary test products become permanent proof artifacts by rename after the per-test size check; each run records original-to-final paths in `artifact_locations.json`. Nothing is discarded or copied as a store/checkpoint. Earlier aborted attempts are retained and are not counted as passes.', '']
for path,p in packages:
    scope='all tree modules' if p.get('all_tree_tests') else 'R2 modules only'
    parts.append('- Package run ('+scope+'): '+str(p.get('tests'))+' tests run, '+str(p.get('discovered','unrecorded'))+' discovered, exit '+str(p['exit_code'])+', '+str(p['failures'])+' failures, '+str(p['errors'])+' errors, '+str(p.get('skips','unrecorded'))+' skips. Source: `'+path+'`. '+('The run stopped before completing its suite. ' if p.get('fatal') or p.get('tests') is None else '')+'A zero or null count is not a pass.')
delta='work/build4/package_final_delta/results.json'
if (L/delta).exists():
    d=read(delta)
    parts.append('- Final extracted-package delta check: '+str(d['tests'])+' tests, '+str(len(d['failures']))+' failures and '+str(len(d['errors']))+' errors. Source: `'+delta+'`. This checks the final grammar wrapper and the corrected environment-clearing harness path; it does not qualify the full suite.')
parts += ['', 'The complete package requirement remains unmet. Legacy tests still require external inputs or subprocess behavior forbidden during this run. The final all-tree attempt reached the lane reserve before its first test. The package bundles the current kits as compressed archives under `work/build4/kits`; the standalone restaged kit directories are also delivered. The earlier R2 suite used the preceding grammar wrapper; final wrapper tests are recorded separately. A prior all-tree run was deliberately interrupted to close the child-process audit boundary; its receipt records the interruption, not a cluster kill.', '']
if coverage:
    parts += ['', 'Changed-statement coverage across the diff from the original base is '+str(coverage['executed'])+'/'+str(coverage['changed_statements'])+'. '+str(coverage['unexecuted'])+' unexecuted statements remain conservatively classified as CPU-reachable unresolved. This fails the requested zero-gap criterion. Source: `work/build4/CHANGED_COVERAGE.json`. Only hash-matched current-file executions count; historical line hits are not assumed valid.']
parts += ['', 'Final artifact identity, required validator/exclusion pins, slice accounting and review-source identity are recorded in `work/build4/FINAL_AUDIT.json`. Resource use is recorded in `work/build4/FINAL_STORAGE.json`. The current tree still refuses readiness; storage limits and missing authorized inputs constrain further proof work.']
parts += ['', '## For the second review', '',
 '- Recheck the current published-row envelope, masked raw pool path, converted-unit and simulated-miss behavior using `work/build4/rows_final_source/RESULTS.json` and the immutable envelopes in `rows_complete`.',
 '- Rerun the row/bank harness and statement mutations from `work/build4/review_harness.py` and `review_mutcov.py`; both preserve original probe bodies/strings where applicable.',
 '- Inspect staging-list completeness separately from actual parent archive/namespace restoration. The latter remains an admission blocker.',
 '- Inspect upload callbacks separately from durable full-state restore. Uploader stand-ins establish ordering and verification, not remote recovery.',
 '- Check final source/config seals and the unsigned authorization before any further work. Empty bank catalog, missing vocabulary and missing component evidence keep this leg closed.', '',
 'Not checked: actual pinned venv/bwrap execution; full parent archive contents and nested native paths; full-store frame-host reconstruction and post-refusal sampler reindexing; actual pretrained vocabulary; real bank membership; real checkpoint restore/upload deadlines/resources; distributed GPU behavior, fit, performance or benchmark results. No source outside the named lane inputs was fetched.', '',
 '## Artifacts', '', 'Tree: `work/tree_r1`. Inventory/diff/seal: `out/TREE_FILES.sha256`, `out/TREE.diff`, `out/TREE_SEAL.json`. Tree digest: `'+seal['tree_sha256']+'` (source: `out/TREE_SEAL.json`).', '']
for k in kit_results:parts.append('- `'+k['kit_path']+'`: `'+k['kit_sha256']+'` (source: `work/build4/kits/RESULTS.json`).')
(L/'out/BUILD4_REPORT.md').write_text('\n'.join(parts)+'\n')
card=['# Prelaunch card','', '**NOT READY; no launch authorization.** Current evidence and limits are in `out/BUILD4_REPORT.md`.', '',
 'The merged withheld list excludes all 80 rooms from every stream, including camera/routing, pose, pointing and the pool. Source: `work/shared/dev_scene_exclusions_d0.json` and the all-stream tests in `work/tree_r1/tests/test_r2_build3b.py`. Its exact binding is a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5 (source: `work/tree_r1/student_pilot/r2_dev_merged.json`).', '',
 'Outputs are planned on node-local disk with durable upload before optional project mirroring. The native guard plans 14 full states plus 2 extra states and 9 exports; source: `work/build4/kits/a0/k/launch.json` → bound config `checkpoint_disk_guard`, checked in `work/build4/KIT_CHECKS.json`. The real upload/restore path remains unqualified.', '',
 'The conservative eval_rooms exclusion applies to every VQA family. The table reports observed slice removals, not full production populations or repeat qualification.', '',repeat,'']
(L/'out/PRELAUNCH_CARD.md').write_text('\n'.join(card))
design=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
section='''\n\n## Build 4\n\nQuestion: Can the repaired tree be admitted after the independent NOT READY review?\n\nAnswer: Not yet. The source now enforces the reviewed intake, provenance, scene, bank, packet, opener and sampling boundaries. Exact runtime staging, durable full-state recovery, the vocabulary witness, package qualification and coverage gaps remain blockers. Current evidence: `out/BUILD4_REPORT.md`, `work/build4/rows_complete/RESULTS.json`, `work/build4/mutation_final/RESULTS.json`, `work/build4/CHANGED_COVERAGE.json`.\n\nReasons: Real published rows now use their own questions, printed events, units and sealed provenance. Contract versions belong to pinned envelopes. Missing clocks, catalog membership and runtime evidence must refuse. Row refusals remain in population denominators.\n\nOptions rejected: Fabricating missing event quantities or clocks would break provenance. Accepting a caller catalog would repeat the review vulnerability. Treating a declared staging entry or fake uploader as a production proof would overstate the evidence. Deleting old proofs would violate the workspace rule; completed products are retained with a location index instead.\n\nWhat might not work and how we notice: Parent archive nesting or namespace dependencies may prevent preparation even after the venv is delivered. Late frame refusals may require sampler reindexing. Remote upload interruption may leave a durable archive without a qualified restore manifest. The gates, package failures and unresolved coverage entries expose these cases rather than granting admission.\n\nTests that would settle it: Stage both kits using the actual pinned runtime and parent archives from empty; reach the named intended refusals under a dependency-free system interpreter; complete full frame-host population/reader checks; exercise trainer-produced checkpoints through upload interruption and restore; supply the vocabulary and bank membership witnesses; obtain a complete package pass and execute every CPU-reachable changed statement.\n\nStatus: NOT READY. No production action is authorized.\n'''
if not design.exists():design.write_text('# Design record\n')
current=design.read_text()
if '\n## Build 4\n' in current:current=current.split('\n## Build 4\n')[0].rstrip()+'\n'
design.write_text(current+section)
print('Report, repeat table, prelaunch card and design record written.')
