"""Write the review report from current, path-bound evidence."""
from pathlib import Path
import ast,hashlib,json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build12';T=L/'work/tree_r1';O=L/'out'
def read(p):return json.loads((L/p).read_text())
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
seal=read('out/TREE_SEAL.json');delivery=read('work/n1fix2/DELIVERY.json')
coverage=read('work/build12/CHANGED_COVERAGE.json');gaps=read('work/build12/GAPS.json')
comparison=read('work/n1fix2/SUITE_COMPARISON.json');kits=read('work/n1fix2/KIT_RESULT.json')
equality=read('work/build12/PROOF_EQUALITY.json');mutants=read('work/build12/proofs/mutations/RESULT.json')['results']
merge=read('work/build12/MERGE12.json')
for row in merge:row['final_sha256']=hashlib.sha256((T/row['file']).read_bytes()).hexdigest()
(B/'MERGE12.json').write_text(json.dumps(merge,indent=2)+'\n')
if '--merge-only' in sys.argv:raise SystemExit(0)
packet=read('work/build12/proofs/n1/packet/results.json')
suites={k:read('work/build12/proofs/n1/suite_'+k+'/results.json') for k in ('tree','base')}
inv=read('work/build12/proofs/inference/INFERENCE_COMPONENTS.json')
known=list(inv['known_outside_forward'])
extra=[('student_pilot/verify_pass.py','Session.ground','Existing exception-to-text conversion can print “chair: not seen” after a head refusal; product acceptance remains blocked.'),
       ('student_pilot/fixed_readout.py','DepthReadout.forward','Parameter-free arithmetic uses fixed buffers; Python/NumPy arithmetic and CPU transfers remain.'),
       ('student_pilot/fixed_readout.py','HeadingReadout.forward','Parameter-free arithmetic uses config-bound threshold and fixed angle buffers.'),
       ('student_pilot/carrier_c1_run.py','load_artifact','Checks artifact hashes, config identity and fixed-readout constants at input load.')]
for file,name,operation in extra:
    parsed=ast.parse((T/file).read_text());parts=name.split('.')
    parent=next((n for n in parsed.body if isinstance(n,ast.ClassDef) and n.name==parts[0]),None) if len(parts)>1 else parsed
    node=next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name==parts[-1])
    known.append(dict(file=file,line=node.lineno,component=name,operation=operation))
inventory_text='# Product inference inventory\n\nThis conservative static import closure includes support and training code. Dynamic dispatch and external dependencies remain unproven.\n\n'
inventory_text+=table(['File:line under work/tree_r1','Component','Classification'],[[r['file']+':'+str(r['line']),r['component'],r['classification']] for r in inv['components']])
(O/'INFERENCE_COMPONENTS_B12.md').write_text(inventory_text)
report=f'''# Build 12

The source, review kits and CPU evidence are packaged with **GO=false**. FRAME64_ALL_READERS_UNQUALIFIED, real P receipt publication, BF16 parity and product-inference acceptance remain blocked. Sources: `work/build12/PROOF_EQUALITY.json`, `work/n1fix2/SUITE_COMPARISON.json`, `work/n1fix2/KIT_RESULT.json`.

Every relative evidence path in this report is rooted at `{L}`. This report distinguishes current proofs from inherited evidence. No launch, remote service, network, GPU, Git, SSH or subagent was used.

## Source and merge

Tree seal: `{seal['tree_sha256']}` over {len(seal['files'])} files (`out/TREE_SEAL.json`). Inventory: `out/TREE_FILES.sha256`; diff against the untouched base: `out/TREE.diff`.

The hash table records n1fix2, n1fix3, build 11, merged and final bytes (`work/build12/MERGE12.json`). The carrier merge preserves every disjoint n1fix3 and build-11 hunk. The base parameter-group builder and n1fix3 training initializer are byte-identical (`work/build12/NATIVE_FUNCTION_EQUALITY.json`).

'''
report+=table(['File','Resolution','Final SHA256'],[[r['file'],r['resolution'],r['final_sha256']] for r in merge])
report+='''
## Findings

'''
findings=[
('n1fix3 merge','Closed','Initialization refusals, independent text checks, optimizer tables and native producer readers pass.','proofs/handover_final/results.json'),
('N1a-3 default deny','Closed','Every config difference outside the documented exact allow-list refuses, including an added null-valued key. P depth_enabled, align and camera changes refuse by name. P topology is constructed from pinned P metadata on meta; the native base group builder compares it with N.','proofs/null_key/results.json; proofs/n1/suite_tree/results.json; NATIVE_FUNCTION_EQUALITY.json'),
('Y5 trainer hook','Closed','The native trainer calls the verifier; replacing the call with None fails the clean regression.','proofs/mutations/RESULT.json'),
('P handover receipt tool and reader','Closed in CPU proof; production publication blocked','The wrapper tool pins export, full-weights manifest and shards, heads, checkpoint completion and all shard/RNG entries, config, binding, preparation, stream receipts and indices. N requires the receipt pin and matching closure. Forged preparation plus forged completion refuses.','proofs/review_final/results.json; proofs/loader_edges/results.json'),
('Unicode class','Closed for authored think text','ASCII-only authored think text refuses the reviewed homoglyphs and unknown non-ASCII characters independently in gate and reader; authenticated printed responses keep their provenance checks. Original-slice verdicts are unchanged.','proofs/text_policy/ASCII_CANDIDATE.json; proofs/n1/row_delta/RESULT.json'),
('Depth initializer paths','Closed as requested','Exact path and hash equality remains. Relocated identical bytes still refuse.','proofs/handover_final/results.json'),
('M1 legacy fixed-buffer binding','Closed at artifact loader','The untouched 9fix producer export loads after config-identity/threshold binding. Missing threshold-bearing identity, mismatched threshold, modern missing buffers and tampered heads refuse. Existing legacy entrypoint admission gates remain in force.','proofs/legacy_export/RESULT.json; proofs/depth_sweep/RESULT.json; proofs/review_final/results.json; proofs/loader_edges/results.json'),
('Re-pinned fixed buffer','Closed','Every fixed-readout buffer is compared with code constants at load; threshold_ratio uses the evaluator config. A re-pinned doubled stencil refuses.','proofs/review_final/results.json'),
('Batch ValueError catch','Closed','Only declared row refusals and CallError are contained. Integrity ValueError propagates in both batch and single-row paths.','proofs/fix_targeted/results.json; proofs/review_final/results.json'),
('Transient restored buffer','Blocked observer limit','EAT1_TRANSIENT_RESTORED_BUFFER_UNOBSERVED: a buffer changed and restored within generate passes A1. Boundary snapshot checks are not continuous integrity.','proofs/observer_limit/RESULT.json'),
('Room reader column','Closed','The room reader column is zero.','proofs/n1/text/RESULT.json'),
('FRAME64_ALL_READERS_UNQUALIFIED','Blocked','Frame-grid admission does not qualify every reader. No qualification claim or gate change.','proofs/n1/kits/RESULT.json'),
('Product inference','Blocked','Existing dispatch, token injection, geometry arithmetic, policies and exception-to-text behavior remain outside weights or outside forward. The acceptance lane must judge them.','proofs/eat1/c8r/run/EAT1_REPORT.json; proofs/inference/INFERENCE_COMPONENTS.json')]
report+=table(['Finding','Status','Behavior','Evidence under work/build12'],findings)
report+='''
## Handover and trusted ledger

P's job wrapper must run `python -m launch_r1.p_handover_receipt --run-pins <pins.json> --artifact <m200/artifact.json> --output <handover.json> --trainer-commit <sealed commit>` inside P's allocation after checkpoint and export publication. `SLURM_JOB_ID` supplies the allocation identity. P's sealed trainer is unchanged.

The operator must immediately record the receipt path and SHA256, P job/allocation id, sealed trainer commit, checkpoint step, export artifact hash and completion hash in the trusted ledger from P's job output. N's reviewed config must pin that ledger-authenticated receipt as `r1_training.handover_receipt`; `p_run` pins must equal the receipt. An operator-created replacement receipt is not an independent trust anchor. No production receipt was written or authenticated in this build (`work/tree_r1/launch_r1/p_handover_receipt.py`; `work/build12/DECISIONS.md`).

The honest fixture and the synthetic P initialized from the pinned 1d6eeb28 artifact admit at step 200; N from its step-544 artifact starts at zero. The parent artifact has no head_init. Actual production P configuration and weights were not supplied (`work/build12/proofs/handover_final/results.json`; `work/build12/proofs/review_final/results.json`).

## CPU proofs and mutation results

The native sealed base export, checkpoint, shard writer, bind_output, wrapper receipt writer and N readers execute end to end. Tiny native model weights stand in for unavailable pretrained GPU weights; local rank/barrier/gather and publication-state boundaries stand in for distributed GPU collectives. Step labels and preparation metadata are synthetic. Only owned proof-file exclusive creation is adapted to overwrite fixed output folders. The RGB proof executes materialization, intake, SQLite reading, RGB loading, routing encoding, forward and backward with synthetic RGB and a tiny native model/tokenizer at the pretrained boundary (`work/build12/proofs/n1/forward/RESULT.json`; `work/tree_r1/tests/test_r2_n1fix.py`; `work/build12/proofs/review_final/results.json`).

The genuine 9fix producer emits 192 head tensors without readout_config. Its bound reader matches 144,000/144,000 review-sweep responses, including invalid-depth responses. Seeded own-head outputs and a float32 query-head stand-in supply the sweep inputs; this is not real-scene parity (`work/build12/proofs/legacy_export/RESULT.json`; `work/build12/proofs/depth_sweep/RESULT.json`).

The modern export/load proof executes an export writer byte-identical to build 11's writer. The load accepts its original buffers and refuses both an independently re-pinned doubled stencil and an old-pin heads-file tamper (`work/build12/NATIVE_FUNCTION_EQUALITY.json`; `work/build12/proofs/review_final/results.json`).

'''
report+=table(['Mutant','Clean','Mutated','Evidence'],[[r['mutant'],'PASS' if r['clean_pass'] else 'FAIL','CAUGHT' if r['caught'] else 'Equivalent; survives','work/build12/proofs/mutations/RESULT.json'] for r in mutants])
report+='\n'+table(['Family','Text','Reader','Intake','Evidence'],[[name,*counts,'work/build12/proofs/n1/text/RESULT.json'] for name,counts in equality['families'].items()])
report+='''
Repaired-family intake counts remain inherited evidence: 777 / 1,476 / 8,067 (`work/n1fix2/inherited/proofs/extent_admission/RESULT.json`). The 601-key exclusion list and division gate are checked locally (`work/build12/proofs/preservation/RESULT.json`). Full repaired-family and production VQA censuses were not rerun. Every original slice is bounded; proofs retain counts/hashes and bounded examples. Text-only normalization retains the disclosed GUESS of 24 FPS where metadata is absent; it does not claim RGB execution (`work/n1fix2/proof_text.py`).

'''
report+=table(['C8r clause','Verdict','Evidence'],[[k,v,'work/build12/proofs/eat1/c8r/run/EAT1_REPORT.json'] for k,v in equality['c8r'].items()])
report+='''
## Suites and coverage

'''
report+=f"Packet suite: {len(packet)} tests, {sum(v['outcome']=='passed' for v in packet.values())} passed (`work/build12/proofs/n1/packet/results.json`).\n\n"
report+=table(['Frozen suite','Executions','Passed','Failure events','Error events','Skips','Evidence'],[[k,v['tests'],len(v['passed']),len(v['failures']),len(v['errors']),len(v['skips']),'work/build12/proofs/n1/suite_'+k+'/results.json'] for k,v in suites.items()])
bf16=[r for r in comparison['failures'] if not r['preexisting'] and 'BF16 cached/online gradient' in r['cause']]
report+=f"\nThe comparison finds {comparison['regressions']-len(bf16)} other regressions, {len(bf16)} retained BF16 parity regression and {comparison['r2_failures']} R2 failures (`work/n1fix2/SUITE_COMPARISON.json`).\n"
report+='\nThe comparison and exact failure classifications are in `work/n1fix2/SUITE_COMPARISON.json`. Base groups reuse receipts only after exact source/fixture hashes and runner equivalence; changed tree groups run from the frozen package. Failure events include subtests and setup errors, so columns need not sum (`work/build12/proofs/n1/suite_base/RESUME_RECEIPT.json`; `work/build12/proofs/n1/suite_tree/*/GROUP_RECEIPT.json`).\n\n'
report+=table(['Coverage class','Changed statements','Evidence'],[[k,v,'work/build12/CHANGED_COVERAGE.json'] for k,v in coverage['classes'].items()])
report+=f'''
CPU-reachable gaps: {len(gaps)} (`work/build12/GAPS.json`). Coverage spans every changed Python statement since the untouched base, excluding the top-level tests directory. Current observations use standard-library monitoring with compiled-source fingerprints and file hashes. Inherited observations require exact file bytes or a byte-identical complete function body, with both source hashes and function hashes recorded. Boundary and unreachable classifications are not execution claims (`work/build12/coverage12.py`; `work/build12/CHANGED_COVERAGE.json`).

The added evaluator binding assignments after preserved unconditional legacy-entry refusals are unreachable. The refusal paths execute in the current CPU proof; the gates were not bypassed to manufacture coverage (`work/build12/proofs/loader_edges/results.json`).

## Product inference outside weights

These existing inference components and input-loading checks are disclosed for lane b03_e2etest. The complete conservative local import inventory, including support functions and literal tables with file:line locations, is `out/INFERENCE_COMPONENTS_B12.md` and `work/build12/proofs/inference/INFERENCE_COMPONENTS.json`. Dynamic dispatch and external dependencies remain unproven. This build adds no fitted answer selector, answer rule table or answer fallback.

'''
report+=table(['Component','File:line under work/tree_r1','Operation'],[[r['component'],r['file']+':'+str(r['line']),r['operation']] for r in known])
report+=f'''
## Delivery

Package: `{delivery['path']}`; gzip; {delivery['bytes']} bytes; SHA256 `{delivery['sha256']}` (`work/n1fix2/DELIVERY.json`).

'''
report+=table(['Kit','SHA256','Authorization','Evidence'],[[k,v['kit_sha256'],'GO=false','work/n1fix2/KIT_RESULT.json'] for k,v in kits.items()])
report+='''
The source inventory, archive, kits and harness patch are checked in `work/build12/FINAL_INTEGRITY.json`. The harness patch is `out/EAT1_FIXED_MATH.patch`; its untouched supplied baseline is pinned in `work/build12/HARNESS_BASE.json`. The explicit merge history is retained because this task requests it; reports otherwise describe current behavior.

## For the confirmation review

- Recompute the source seal, inventory, base diff, package hash and kit hashes. Inspect the per-file merge and the byte-identical native group builder and initializer.
- Replay P depth_enabled, align and camera differences; verify the config allow-list and that P's meta model comes from authenticated P metadata. Check the honest continuation, parent initializer and trainer-hook mutation.
- Run the wrapper receipt producer and N reader against native CPU checkpoint/export outputs. Forge both preparation and completion while keeping the trusted receipt pin; confirm refusal. Verify every referenced shard, RNG, stream and index pin. A production P receipt still needs trusted-ledger publication.
- Replay the genuine 9fix export load, threshold mismatch, missing modern buffers, re-pinned doubled stencil and old-pin heads tamper. Compare the review sweep bytes. Existing legacy evaluation admission refusals remain.
- Verify Unicode refusals independently in gate and reader and unchanged original-slice verdicts. Check the room reader column, inherited repaired counts, exclusion list and division gate.
- Check typed batch refusals and propagated integrity errors, mutation receipts, frozen-group resume keys, baseline comparison and every coverage classification. Inspect the explicit transient-buffer observer limit.
- Keep FRAME64_ALL_READERS_UNQUALIFIED, BF16 parity, bound-real-row numeric parity, production P staging, GPU/pretrained execution and deployed product-inference acceptance blocked. Neither full stores nor production checkpoints were copied; no launch was attempted.
'''
(O/'BUILD12_REPORT.md').write_text(report)
design=O/'DESIGN_RECORD_tree_rebuild_20261115.md';text=design.read_text()
section='\n\n## Build 12\n\nThe source uses default-deny P/N config comparison, P-derived meta topology, a wrapper-written trusted handover receipt, ASCII-only authored think text, config-bound legacy readout constants and typed batch refusals. The native initializer and base group builder retain their bytes. GO=false; all acceptance blockers remain. Full evidence and delivery hashes: `BUILD12_REPORT.md`, `TREE_SEAL.json`, and `../work/build12/FINAL_INTEGRITY.json`.\n'
if '\n## Build 12\n' in text:text=text.split('\n## Build 12\n')[0].rstrip()
design.write_text(text+section)
print(json.dumps(dict(report=str(O/'BUILD12_REPORT.md'),coverage=coverage['classes'],cpu_gaps=len(gaps),comparison=comparison.get('counts',comparison.get('summary',{})))))
