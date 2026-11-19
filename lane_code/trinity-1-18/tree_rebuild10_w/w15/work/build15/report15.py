from pathlib import Path
import json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build15'
def load(p):return json.loads((L/p).read_text())
real=load('work/build15/proofs/real/RESULT.json')
tests=load('work/build15/proofs/final_focused/TESTS.json')
assert tests['successful']
delta=load('work/build15/DELTA_COVERAGE.json');assert delta['observed']==delta['total']
kits=load('work/build15/KIT_RESULT.json')
seal=load('out/TREE_SEAL.json')['tree_sha256']
packet=load('work/build15/proofs/final/packet/results.json')
suite=load('work/build15/proofs/final/suite_tree/r2/results.json')
preserve=load('work/build15/PRESERVATION.json')
text=load('work/build15/proofs/text/RESULT.json');prior=load('work/build14/proofs/text/RESULT.json')
# Preserve the original-family census values without relabeling historical census runs.
assert text.keys()==prior.keys()
def counts(x):
    if isinstance(x,dict):return {k:counts(v) for k,v in x.items() if k not in ('source','path')}
    if isinstance(x,list):return [counts(v) for v in x]
    return x
assert counts(text)==counts(prior)
removal=load('work/build15/proofs/preservation/RESULT.json');assert removal['keys']==601
eq=dict(original_family_counts_equal=True,source='work/build15/proofs/text/RESULT.json',
    baseline='work/build14/proofs/text/RESULT.json',exclusion_keys=removal['keys'],
    exclusions_source='work/build15/proofs/preservation/RESULT.json',
    historical_census='work/build14/proofs/census/CENSUS.json',
    historical_census_sha256=hashlib.sha256((L/'work/build14/proofs/census/CENSUS.json').read_bytes()).hexdigest(),
    historical_plan='work/build14/proofs/census/PLAN_RUN.json',
    historical_plan_sha256=hashlib.sha256((L/'work/build14/proofs/census/PLAN_RUN.json').read_bytes()).hexdigest())
(B/'COUNT_EQUALITY.json').write_text(json.dumps(eq,indent=2))
report=['# Build 15','',
'**A, C and C′ admit. N must keep opener rows when initialized from P’s export. GO=false remains.** '
'The requested comparator and CPU witness proofs pass. The broader qualification remains partial because external inputs are absent and the packet generator has an exact floating-point serialization mismatch. '
'Sources: `work/build15/proofs/real/RESULT.json`, `work/build15/proofs/final_focused/TESTS.json`, `work/build15/proofs/final/packet/results.json`, `work/build15/SUITE_RUNS.json`.','',
'## Handover and witness','',
'`routing_opener_init` describes each run’s own initialization boundary. P’s recorded value does not constrain N. '
'N must use `keep`; explicit `reset` and omission with a P export refuse with '
'`P_EXPORT_ROUTING_OPENER_KEEP_REQUIRED:routing_opener_init`. The comparator, native preparation, native opener initializer and continuation reader exercise this refusal. '
'The parent initialization path retains its existing behavior. Sources: `work/tree_r1/student_pilot/r1_handover.py`, '
'`work/tree_r1/student_pilot/r2_openers.py`, `work/build15/proofs/final_focused/n1fix/b15_witness/RESULT.json`.','',
'The operator supplies **`v.json`, produced by `launch_r1.p_opener_witness`**, as an exact path/SHA-256 pin in N’s `routing_vocabulary`. '
'The producer authenticates P’s run and handover receipt closure, verifies P’s pinned parent artifact, and reconstructs P’s vocabulary from its authenticated preparation/model manifest and pinned tokenizer metadata using the native `processor_for_receipt` token setup. '
'This supports the legacy P exporter, which records neither `routing_vocabulary` nor `r2_identity`. An optional vocabulary declaration in a newer export must agree. '
'The witness binds `artifact_sha256` to P’s export, `lineage_sha256` to the step-544 parent, and records the vocabulary digest, opener IDs and constituent IDs. '
'Sources: `work/tree_r1/launch_r1/p_opener_witness.py`, `work/base/tree_b01ce449/student_pilot/carrier_c1_run.py`, `work/build15/proofs/witness_edges/RESULT.json`.','',
'Generate the witness after P’s export and handover receipt exist. Then set N’s `routing_vocabulary` pin and produce N’s continuation identity and handover mapping. '
'N’s unchanged preparation reader validates the artifact/lineage binding; its initializer compares the live vocabulary and preserves the input and output opener rows. '
'The producer requires P’s actual preparation and tokenizer files; it does not use N’s tokenizer as evidence for P. '
'Sources: `work/tree_r1/launch_r1/p_opener_witness.py`, `work/tree_r1/student_pilot/r2_openers.py`.','',
'```bash',
'# Run in the authenticated operator environment with the sealed tree on PYTHONPATH.',
'python -m launch_r1.p_opener_witness --config /path/to/n.json --output /path/to/v.json',
'```','',
'The CPU proof runs the legacy native checkpoint/export, handover receipt producer, witness producer, LM artifact loader, preparation reader and opener initializer. '
'A tiny native CPU model and local tokenizer replace pretrained GPU assets; local collectives replace distributed publication. '
'Both opener embedding rows remain equal after loading and keeping. Wrong artifact, lineage, vocabulary, token IDs, missing witness and N reset refuse. '
'No real P export weights or production tokenizer were supplied or inspected. '
'Sources: `work/build15/proofs/final_focused/n1fix/b15_witness/RESULT.json`, `work/build15/proofs/witness_edges/RESULT.json`.','',
'## Real configurations','',
'| Config | Computed tree configuration identity | Result |','|---|---|---|']
for name,r in real['real'].items():report.append(f"| {name} | `{r['config_identity']}` | {r['result']} |")
report += ['',
'Source: `work/build15/proofs/real/RESULT.json`. C′ equals the supplied `774503e2...` identity prefix; the computed full identity is shown above. '
'A/C and the preparation receipt retain their full SHA-256 pins. C′ file bytes bind to `31abe0871f35f9ca8d4a6445c5ee95ac03ec2324d37273e6b1f508acdbf246a1`. '
'N’s local metadata replicas retain the original hashes; only their paths changed. Sources: `work/build15/LOCAL_PINS.json`, `work/build15/proofs/real/RESULT.json`.','',
'| Mutation | Named refusal, identical for A/C/C′ |','|---|---|']
for k,v in real['refuse']['A'].items():report.append(f'| `{k}` | `{v}` |')
report += ['',
'Source: `work/build15/proofs/real/RESULT.json`. The camera mutation increases the authenticated trunk depth by two; the camera-weight mutation changes the scale weight. The native CPU fixture additionally tests reset against an actual P-export init.','',
'## Verification and preserved behavior','',
f"Focused tests: **{tests['tests']} passed**. Source: `work/build15/proofs/final_focused/TESTS.json`.",
f"Frozen R2 group: **{suite['tests']} tests, {len(suite['passed'])} passed, {len(suite['failures'])} failures, {len(suite['errors'])} errors, {len(suite['skips'])} skipped**. Source: `work/build15/proofs/final/suite_tree/r2/results.json`.",
f"Packet checks: **{sum(v['outcome']=='passed' for v in packet.values())} passed**. Source: `work/build15/proofs/final/packet/results.json`.",
'',
'The frozen R2 result combines its initial run with the targeted rerun of three tests after restoring access to exact packaged metadata. No source or test assertion changed. '
'The initial results, input hashes and rerun are bound in `work/build15/proofs/final/suite_tree/r2/RESUME_RECEIPT.json`.',
'',
'The packet check `test_production_generator_on_off` fails an exact JSON comparison at the last printed floating-point digit. The generator source and baseline fixture are unchanged. '
'This is an observed failure under the supplied CPU environment, not a pass or a changed tolerance. '
'`test_decode_attacks_and_move_source_distance` could not execute its assertion: input absent '
'(`/scratch/jjyeung/orch_n30/review_contracts/work/mytests/attack_decode.py`). '
'Sources: `work/build15/proofs/final/packet/results.json`, `work/build15/proofs/packet/console.log`, `work/build15/PRESERVATION.json`.','',
'The original-family read/reader/intake counts remain 1532/0/0, 2000/1186/1102, 2000/1222/1119 and 476/0/431. '
'The exact 601-row exclusion list passes again. Sources: `work/build15/proofs/text/RESULT.json`, `work/build15/proofs/row_delta/RESULT.json`, '
'`work/build15/proofs/preservation/RESULT.json`, `work/build15/COUNT_EQUALITY.json`.','',
'The six population/routing guard mutations are caught with one reused mutant tree. Receipt closure, default deny, Unicode rules, M1 fixed-buffer binding, '
'L1 typed refusals, effective-value comparison and milestone-step continuation remain covered by the focused and R2 suites. '
'Sources: `work/build15/proofs/mutations/RESULT.json`, `work/build15/proofs/final_focused/TESTS.json`, `work/build15/proofs/final/suite_tree/r2/results.json`.','',
'N retains its step-544 parent (`1d6eeb28...`), scale weight `0.04`, and all sealed scene exclusions. '
'The prior repaired counts 777/1476/8067 and complete allocation table remain historical census evidence; the absent raw inputs prevent a new census. '
'The qualification and hashes of each retained result appear in `work/build15/PRESERVATION.json`; unqualified records are retained only as historical records. '
'Sources: `work/build15/inputs/kit_config.json`, `work/build14/proofs/census/CENSUS.json`, `work/build14/proofs/census/PLAN_RUN.json`, `work/build15/COUNT_EQUALITY.json`.','',
'## Inputs not available','']
for name,r in preserve['unavailable'].items():report.append(f"- {name}: {r['status']}. Prior-result qualification: {r['inherited_result_qualified']}; no build-15 pass.")
for name,r in load('work/build15/SUITE_RUNS.json').items():
    if 'status' in r:report.append(f"- {name} suite group: {r['status']}. Its full source binding changed, so no prior suite pass transfers.")
report += ['',
'Sources: `work/build15/PRESERVATION.json`, `work/build15/INPUT_AVAILABILITY.json`, `work/build15/SUITE_RUNS.json`. '
'No missing data were fabricated or substituted. The inherited full parity sweep is not counted as a build-15 pass.','',
'## Coverage, seal and delivery','',
f"Current observations cover **{delta['observed']}/{delta['total']} changed production statement heads against build 14**.",
'The standard-library monitor authenticates compiled code and exact source hashes. Cumulative coverage against the original tree, including inherited observations, is separate. '
'Sources: `work/build15/DELTA_COVERAGE.json`, `work/build15/CHANGED_COVERAGE.json`, `work/build15/GAPS.json`.','',
f"Source seal: `{seal}`. Archive: `out/tree_rebuild_b15_{seal[:8]}.tar` (gzip). Archive size and SHA-256 are recorded in `work/build15/DELIVERY.json`; stream verification is recorded in `work/build15/proofs/integrity/RESULT.json`.",
'Sources: `out/TREE_SEAL.json`, `out/TREE_FILES.sha256`, `out/TREE.diff`.','',
'| Kit | SHA-256 | GO |','|---|---|---|']
for name,r in kits.items():report.append(f"| {name} | `{r['kit_sha256']}` | false |")
report += ['',
'Source: `work/build15/KIT_RESULT.json`. Each kit was staged from empty and passed its existing scanner and hash verifier. '
'No job was submitted. Production admission, full frame-host staging, GPU/pretrained execution, BF16 parity and the prior product-inference blockers remain unchecked or unresolved. '
'No model, inference selector, fallback, agent loop or training-data quota changed.','',
'Storage and temporary-size checks are recorded in `work/build15/STORAGE.json`, per-test storage receipts and the final integrity receipt. '
'All proof writes stay under this workspace. No checkpoint, database, cache or frame set was copied from an external input.','',
'## For the confirmation','',
'Run from the package root using the supplied CPU environment. These commands retain proof outputs in fixed folders. Missing-input qualifications remain explicit.','',
'```bash',
'bash work/build15/run.sh work/build15/real15.py',
'bash work/build15/run.sh work/build15/opener15.py',
'B15_PROOF=final_focused bash work/build15/run.sh work/build15/test15.py tests.test_r1_build15 tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13 tests.test_r2_build3.Build3.test_opener_export_keep_and_reset',
'bash work/build15/run.sh work/build15/witness_edges15.py',
'bash work/build15/run.sh work/build15/proofs15.py text row_delta preservation confusables mutations ground_runtime verify_route',
'bash work/build15/run.sh work/build15/preserve15.py',
'bash work/build15/run.sh work/build15/suite15.py',
'bash work/build15/run.sh work/build15/packet_inputs15.py',
'bash work/build15/run.sh work/build15/packet15.py integrated packet contract',
'bash work/build15/run.sh work/build15/delta_coverage15.py',
'bash work/build15/run.sh work/build15/coverage15.py',
'bash work/build15/run.sh work/build15/integrity15.py',
'```','',
'The packet command currently records the qualified failures above. Use `kits15.py` only with an empty kit destination; `integrity15.py` verifies the retained kits. '
'`delivery15.py` packages the final source and evidence. `localize15.py` is a build-time relocation step, not a routine confirmation command.','']
(L/'out/BUILD15_REPORT.md').write_text('\n'.join(report).replace(" '.\n",'.\n').replace(". '\n",'.\n'))
design=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md';s=design.read_text();s=s.split('\n## Build 15\n')[0]
s+='\n## Build 15\n\nP’s routing opener policy describes its own parent initialization. N uses `keep` for a P-export init; reset and omission refuse by name. '
s+='The new `launch_r1.p_opener_witness` producer authenticates P’s export closure and pinned preparation/tokenizer metadata, reconstructs the native vocabulary, and binds the witness to P’s export and the step-544 lineage. '
s+='The operator pins that witness before producing N’s continuation identity and mapping. The native CPU export/load proof preserves both opener rows. '
s+='A, C and Cprime admit; Cprime computes to `'+real['real']['Cprime']['config_identity']+'`. '
s+='Sources: `work/build15/proofs/real/RESULT.json`, `work/build15/proofs/final_focused/n1fix/b15_witness/RESULT.json`, `work/build15/proofs/witness_edges/RESULT.json`.\n\n'
s+='N’s parent, scale weight, exclusions, row counts, receipt checks and inference behavior remain unchanged. Missing inputs and the packet floating-point comparison failure keep qualification partial and GO=false. '
s+='Results, source pins, confirmation commands and unchecked production boundaries are in `out/BUILD15_REPORT.md`.\n'
design.write_text(s)
(B/'STATUS.md').write_text('# Build 15 status\n\nA/C/Cprime admit; the native opener witness and preservation proofs pass. GO=false. Final archive integrity is pending. Missing inputs and the packet comparison failure remain explicit in out/BUILD15_REPORT.md.\n')
print('Wrote report and Build 15 design section.')
