from pathlib import Path
import ast,difflib,hashlib,json
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';N=L/'work/n1fix2';T=L/'work/tree_r1'
def read(p):return json.loads((L/p).read_text())
def ev(p):return '`'+p+'`'
seal=read('out/TREE_SEAL.json');delivery=read('work/n1fix2/DELIVERY.json')
changes=read('work/merge11/CHANGESETS.json');coverage=read('work/merge11/CHANGED_COVERAGE.json')
comparison=read('work/n1fix2/SUITE_COMPARISON.json');kits=read('work/n1fix2/KIT_RESULT.json')
equality=read('work/merge11/PROOF_EQUALITY.json');sweep=read('work/merge11/proofs/depth_sweep/RESULT.json')
text=read('work/merge11/proofs/n1/text/RESULT.json');packet=read('work/merge11/proofs/n1/packet/results.json')
inventory=read('work/merge11/proofs/inference/INFERENCE_COMPONENTS.json')
# Keep the patch relative to the untouched supplied harness.
base=L.parent/'work/design/eat1_v7/eat1';patch=[]
for p in sorted((L/'work/build10/eat1').rglob('*.py')):
    name=p.relative_to(L/'work/build10/eat1');prior=base/name
    a=prior.read_text().splitlines(True) if prior.exists() else []
    patch.extend(difflib.unified_diff(a,p.read_text().splitlines(True),fromfile='a/eat1/'+str(name),tofile='b/eat1/'+str(name)))
(L/'out/EAT1_FIXED_MATH.patch').write_text(''.join(patch))
(B/'PATCH.json').write_text(json.dumps(dict(path='out/EAT1_FIXED_MATH.patch',sha256=hashlib.sha256((L/'out/EAT1_FIXED_MATH.patch').read_bytes()).hexdigest()),indent=2)+'\n')
lines=['# Build 11 (merge)','',
'The merged vehicle-N source and kits are ready for independent review with **GO=false**. This is not product-inference acceptance or launch authorization. The acceptance blockers, including FRAME64_ALL_READERS_UNQUALIFIED, remain. Sources: `work/merge11/PROOF_EQUALITY.json`, `work/n1fix2/KIT_RESULT.json`, and `work/merge11/CHANGED_COVERAGE.json`.','',
'Relative evidence paths are rooted at '+ev(str(L))+'.','',
'## Source and merge','',
'Tree seal: '+ev(seal['tree_sha256'])+'; inventory: `out/TREE_FILES.sha256`; base diff: `out/TREE.diff`; source: `out/TREE_SEAL.json`.','',
'The hash-based change sets, per-file input hashes and intersection are in `work/merge11/CHANGESETS.json`. The shared-file merge is recorded in `work/merge11/MERGE_TABLE.json`.','',
'| File | Build 10 | n1fix2 | Resolution |','|---|---|---|---|']
left=set(changes['build10']['added']+changes['build10']['changed']);right=set(changes['n1fix2']['added']+changes['n1fix2']['changed'])
for name in sorted(left|right):
    how=('Keep N’s R0 reservation and all readout initialization/export/admission changes.' if name in left&right else 'Carry build 10 bytes; apply only the listed review fix where required.' if name in left else 'Retain N behavior.')
    lines.append('| '+ev(name)+' | '+('changed' if name in left else 'unchanged')+' | '+('changed' if name in right else 'unchanged')+' | '+how+' |')
lines+=['','The handover, training contract, independent normalized reader, launch admission and per-job temporary-namespace source files remain byte-identical to n1fix2 (`work/merge11/N_BEHAVIOR_PRESERVED.json`). The training init function also remains byte-identical (`work/merge11/INIT_UNCHANGED.json`). Test fixture paths are localized; the R1 mix was not redesigned.','',
'## Review fixes','',
'| Finding | Behavior and evidence |','|---|---|',
'| M1 | A genuine native export in the 9fix format refuses explicitly with `LEGACY_READOUT_EXPORT_UNSUPPORTED` when fixed-readout buffers are absent. An export declaring the modern config but missing buffers refuses with `ARTIFACT_READOUT_BUFFERS_MISSING`. Tiny native weights and local distributed-boundary stand-ins are used by the real export producer; no production P or step-544 weights were loaded. `work/merge11/proofs/review_tests/results.json`; `work/tree_r1/tests/test_merge11.py`; `work/merge11/legacy9fix_source.py`. |',
'| M2 | Invalid own depth raises RenderError and prints the original text, then decoding can continue. The reviewer’s saved 9fix sweep matches byte-for-byte: '+str(sweep['counts']['identical'])+' identical responses and '+str(sweep['counts']['different'])+' differences, including '+str(sweep['counts']['invalid_depth'])+' invalid-depth responses. `work/merge11/proofs/depth_sweep/RESULT.json`. |',
'| M3 | Changed production statements are observed or retain explicit external-boundary classifications. CPU gaps: '+str(len(read('work/merge11/GAPS.json')))+'. `work/merge11/CHANGED_COVERAGE.json`; `work/merge11/GAPS.json`. |',
'| L1 | The EAT-1 observer checks fixed_math buffers again at run end. A buffer changed inside generate fails A1. `work/merge11/proofs/l1/RESULT.json`; `work/build10/eat1/run.py`; `out/EAT1_FIXED_MATH.patch`. |',
'| L2 | A batch row’s ValueError refusal produces a row-local refusal record; other rows complete. No response tokens are fabricated for the refused call. Budget, invalid-frame and impersonation cases are covered. `work/merge11/proofs/review_tests/results.json`; `work/tree_r1/tests/test_batched_routed_decode.py`. |','',
'The named legacy-export refusal is the selected default in `work/merge11/DECISIONS.md`; it does not qualify legacy export evaluation. FRAME64_ALL_READERS_UNQUALIFIED remains: the admitted grid shape does not qualify every contract/calculator reader.','',
'## Proofs and suites','',
'Build-10 available numeric parity and the EAT-1 clause tables match their source receipts (`work/merge11/PROOF_EQUALITY.json`). Bound-row numeric parity remains blocked because the slices lack the producer operands (`work/merge11/proofs/parity/BYTE_PARITY.json`). The reviewer sweep uses seeded own-head outputs and a float32 head stand-in; it is not real-scene parity (`work/merge11/proofs/depth_sweep/RESULT.json`).','',
'| Reader | A1 | A2 | A3 | A4 | A5 | A6 | Evidence |','|---|---|---|---|---|---|---|---|']
for name,clauses in equality['eat1'].items():lines.append('| '+name+' | '+' | '.join(clauses[k] for k in ('A1','A2','A3','A4','A5','A6'))+' | '+ev('work/merge11/proofs/eat1/'+name+'/run/EAT1_REPORT.json')+' |')
lines+=['','These are harness verdicts. b04’s A2 pass covers an early-failing path whose routed items refuse `sealed_validate_mismatch`; it does not establish successful routed inference. Native readers use tiny native weights and scripted LM policies. b04 uses supplied trained heads mounted read-only, captured tower-boundary outputs and a tiny generated LM (`work/merge11/proofs/eat1/b04/MOUNTS.json`).','',
'The real producer-to-reader RGB proof runs materialization, intake, SQLite reading, RGB loading, routing encoding, model forward and backward. Tiny native pretrained-boundary weights and a lossless tokenizer/processor stand in at the unavailable pretrained/GPU boundary; RGB is synthetic. Details, loss and gradients: `work/merge11/proofs/n1/forward/RESULT.json`. Native export/checkpoint production and handover readers also execute with local rank/collective stand-ins (`work/merge11/proofs/n1/checkpoint/RESULT.json`).','',
'M07, M09, M12, H2 and H6 all pass their clean oracle and are caught when mutated (`work/merge11/proofs/n1/mutations/RESULT.json`). The original-family text, reader and intake outcomes follow.','',
'| Family | Text | Reader | Intake | Evidence |','|---|---:|---:|---:|---|']
families=text.get('families',text.get('results',text))
for name in ('a0_recovery','a0_units','a0_pool_abs_distance_reworded','a0_room'):
    c=families[name]['counts'];lines.append('| '+name+' | '+str(c['text'])+' | '+str(c['reader'])+' | '+str(c['intake'])+' | `work/merge11/proofs/n1/text/RESULT.json` |')
lines+=['','Repaired-family intake counts remain inherited evidence: 777 / 1,476 / 8,067 (`work/n1fix2/inherited/proofs/extent_admission/RESULT.json`). The 601-key exclusion list and division refusal are checked locally (`work/merge11/proofs/preservation/RESULT.json`). Neither full-family census was rerun. Row text proofs retain the disclosed GUESS of 24 FPS where metadata is absent; these proofs do not claim RGB execution (`work/n1fix2/proof_text.py`).','',
'Packet suite: '+str(len(packet))+' tests, '+str(sum(v['outcome']=='passed' for v in packet.values()))+' passed (`work/merge11/proofs/n1/packet/results.json`).','',
'| Frozen suite | Executions | Passed | Failure events | Error events | Skips | Evidence |','|---|---:|---:|---:|---:|---:|---|']
for variant in ('tree','base'):
    path='work/merge11/proofs/n1/suite_'+variant+'/results.json';v=read(path)
    lines.append('| '+variant+' | '+str(v['tests'])+' | '+str(len(v['passed']))+' | '+str(len(v['failures']))+' | '+str(len(v['errors']))+' | '+str(len(v['skips']))+' | '+ev(path)+' |')
lines+=['','Regression events: '+str(comparison['regressions'])+'; R2 failure events: '+str(comparison['r2_failures'])+' (`work/n1fix2/SUITE_COMPARISON.json`). The retained BF16 cached/online parity failure does not qualify BF16 use. Failure events include subtests and setup errors, so they need not sum to executions. Frozen groups bind source and fixture hashes; unchanged base evidence is reused only after runner equivalence checks (`work/merge11/BASE_REUSE.json`, `work/merge11/proofs/n1/suite_base/RESUME_RECEIPT.json`).','',
'## Changed-statement coverage','',
'Standard-library monitoring requires current file hashes and compiled-code fingerprints. Coverage spans production changes since the untouched base. External-boundary classes are limitations, not execution claims (`work/merge11/coverage.py`, `work/merge11/CHANGED_COVERAGE.json`).','',
'| Class | Statements | Evidence |','|---|---:|---|']
for name,count in coverage['classes'].items():lines.append('| '+name+' | '+str(count)+' | `work/merge11/CHANGED_COVERAGE.json` |')
lines+=['','Harness coverage is recorded separately in `work/merge11/HARNESS_COVERAGE.json`.','',
'## Product inference outside learned weights','',
'The acceptance lane must judge the current inference path. The following known components execute outside learned weights or outside the model forward. The complete conservative static inventory, including support functions, is in `out/INFERENCE_COMPONENTS_B11.md` and `work/merge11/proofs/inference/INFERENCE_COMPONENTS.json`. Dynamic dispatch and external dependencies remain unproven.','',
'| Component | Source under work/tree_r1 | Operation |','|---|---|---|']
for r in inventory['known_outside_forward']:lines.append('| '+ev(r['component'])+' | '+ev(r['file']+':'+str(r['line']))+' | '+r['operation']+' |')
for file,cls in [('student_pilot/fixed_readout.py','DepthReadout'),('student_pilot/fixed_readout.py','HeadingReadout')]:
    node=next(n for n in ast.parse((T/file).read_text()).body if isinstance(n,ast.ClassDef) and n.name==cls)
    fn=next(n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
    lines.append('| '+cls+'.forward | '+ev(file+':'+str(fn.lineno))+' | Registered zero-parameter arithmetic uses artifact-bound buffers; Python/NumPy arithmetic and CPU transfers remain. |')
lines+=['','Existing selectors, policies, route dispatch, response serialization and token injection are disclosed for acceptance review. This build adds no fitted selector, answer-selection table or answer fallback.','',
'## Artifacts','',
'Package: '+ev(delivery['path'])+'; SHA256 '+ev(delivery['sha256'])+'; '+str(delivery['bytes'])+' bytes, gzip-compressed (`work/n1fix2/DELIVERY.json`).','',
'| Kit | SHA256 | Evidence |','|---|---|---|']
for name,v in kits.items():lines.append('| '+name+' | '+ev(v['kit_sha256'])+' | `work/n1fix2/KIT_RESULT.json` |')
lines+=['','Kits are unsubmitted and GO=false. Archive verification and frozen kit checks: `work/merge11/proofs/n1/package/ARCHIVE.json` and `work/merge11/proofs/n1/package/KIT_TESTS.json`. Storage census: `work/merge11/STORAGE.json`.','',
'## For the review','',
'- Recompute the source seal, archive hash, kit hashes and patched-harness diff; compare both input change sets and the shared-file merge.','- Replay the genuine legacy-format export refusal and verify that the training init function remains byte-identical. Check the invalid-depth sweep hashes and row-local batch refusals.','- Check buffer equality after generate, all mutation receipts, exact-source coverage and remaining boundary classifications.','- Preserve every exclusion and the division gate. Full repaired-family and production VQA censuses were not rerun.','- Keep EAT-1 acceptance, bound-row numeric parity, frame-64 reader qualification, real P handover, production staging and GPU/pretrained execution blocked. BF16 parity remains unqualified.','',
'No launch, Orchard/GCS call, network request, GPU operation, Git command or subagent was used. Writes stay within this workspace. The requested build comparisons and per-file merge history are retained as explicit review evidence under the no-archaeology skill exception for this task.','']
(L/'out/BUILD11_REPORT.md').write_text('\n'.join(lines))
details=['# Conservative inference component inventory','','This inventory includes support/training imports; it is not a claim that every entry executes in inference. Each source hash is bound in `work/merge11/proofs/inference/INFERENCE_COMPONENTS.json`.','','| Component | Source under work/tree_r1 | Classification |','|---|---|---|']
for r in inventory['components']:details.append('| '+r['component'].replace('|','\\|')+' | '+r['file']+':'+str(r['line'])+' | '+r['classification']+' |')
(L/'out/INFERENCE_COMPONENTS_B11.md').write_text('\n'.join(details)+'\n')
p=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md';prior=p.read_text().split('\n## Build 11 (merge)\n')[0]
p.write_text(prior+'\n## Build 11 (merge)\n\nVehicle N uses the merged source sealed as `'+seal['tree_sha256']+'`. Kits remain GO=false. The review fixes restore invalid-depth text, make legacy export incompatibility explicit, isolate batch-row refusals and recheck harness buffers after generation. Evidence and remaining acceptance blockers: `out/BUILD11_REPORT.md`, `work/merge11/PROOF_EQUALITY.json`, `work/merge11/CHANGED_COVERAGE.json`, and `work/n1fix2/SUITE_COMPARISON.json`.\n')
(B/'STATUS.md').write_text('# Build 11 status\n\nAll requested merge and qualification steps are recorded. GO=false. Final report: ../../out/BUILD11_REPORT.md. Source: ../../out/TREE_SEAL.json. Package receipt: ../n1fix2/DELIVERY.json. CPU coverage and regression details: CHANGED_COVERAGE.json and ../n1fix2/SUITE_COMPARISON.json.\n')
print('Final report and design record written.')
