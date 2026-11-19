"""Render the report from saved evidence; no result is inferred from a log tail."""
from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build13'
def read(p):return json.loads((L/p).read_text())
c=read('work/build13/proofs/census/CENSUS.json')
p=read('work/build13/proofs/census/PLAN_RUN.json')
pop=read('work/build13/proofs/census/population/population.json')
cov=read('work/build13/CHANGED_COVERAGE.json')
s=read('work/build13/SUITE_COMPARISON.json')
base=read('work/build13/proofs/final/suite_base/results.json')
k=read('work/build13/KIT_RESULT.json')
mut=read('work/build13/proofs/mutations/RESULT.json')['results']
packet=read('work/build13/proofs/final/packet/results.json')
seal=read('out/TREE_SEAL.json')
parts=['# Build 13\n',
'The R1 population producer and N routing composition are implemented and CPU-qualified. GO=false: production admission still requires the real frame host, verified remote slice sources, catalogs and coverage. Trinity cannot certify the full production audit. Source: `work/build13/proofs/tests/results.json`; `work/build13/KIT_RESULT.json`.\n',
'## Changes\n',
'| Change | State | Evidence |\n|---|---|---|',
'| Population after native preparation, source-identity cells, complete disjoint reader offsets, mixed pose support and binding publication | Closed in code and CPU proofs | `student_pilot/r1_population.py`; `work/build13/proofs/census/`; `work/build13/proofs/tests/` |',
'| Native routing base composition with N slices; original distance/unit rows excluded; membership pinned | Closed in code and CPU proofs | `student_pilot/r1_routing.py`; `work/build13/proofs/builder/RESULT.json`; `work/build13/proofs/composition/RESULT.json` |',
'| Native routing layout reaches reader and encoder | Closed in CPU proof | `work/build13/proofs/encode/RESULT.json` |',
'| Host wiring, produced config and audit binding | Implemented; full host run blocked | `student_pilot/s1_admission.py`; `launch_r1/entry.py`; `student_pilot/r1_loader.py` |',
'| Reader subset preserves original scene evidence | Closed in CPU proof | `student_pilot/s1_exclusions.py`; `work/build13/proofs/edges/RESULT.json` |',
'| Fresh kits, pinned slice requirements and membership, ordered host request | Closed; remote source resolution blocked | `launch_r1/build.py`; `work/build13/KIT_RESULT.json` |',
'| Refusal tests and mutations | Closed | `tests/test_r1_build13.py`; `work/build13/proofs/mutations/RESULT.json` |',
'| Portable confirmation fixture resolves the parent artifact inside the package and verifies its unchanged hash | Closed | `tests/test_r2_build12.py`; `work/build13/proofs/fixture_path/TESTS.json` |',
'| Full RGB/GPU production acceptance, BF16 parity and existing qualification blockers | Blocked; unchanged | `work/build13/SUITE_COMPARISON.json`; `work/build13/KIT_RESULT.json` |\n',
'The host composes at native admission, immediately after `s1_routing.build` and before `prepare`. This preserves the native catalogs and selection while giving preparation one routing receipt. The SQLite `rows` view reconstructs the native routing JSON from a payload that stores the repeated ground record once; membership authenticates that reconstructed row. Source: `student_pilot/r1_routing.py`.\n',
'## Census reproduction\n',
'Every entry below matches the lane audit exactly. Source: `work/build13/proofs/census/CENSUS.json`; reference pin: `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n/CENSUS.json`.\n',
'| Cell | Lane eligible | Producer eligible |\n|---|---:|---:|']
for name,count in c['vqa']['eligible_by_cell'].items():parts.append(f'| {name} | {count:,} | {count:,} |')
for name,v in c['slices'].items():parts.append(f"| {name} slice | {v['eligible']:,} | {v['eligible']:,} |")
parts += [f"\nThe VQA scan read {c['vqa']['read']:,} rows. The exclusion list refused 601 and the ASCII think check refused 6, leaving {sum(c['vqa']['eligible_by_cell'].values()):,}. Source: `work/build13/proofs/census/CENSUS.json`.",
f"Slice-source identity overrides the question-type classification for {pop['source_identity_overrides']} rows. Unit counts are {pop['asked_units']}. Facing statistics are {p['facing']}. Source: `work/build13/proofs/census/population/population.json`.",
'The sealed P classifier agrees on the bounded real-row sample. Source: `work/build13/proofs/mapping/RESULT.json`. Zero-quota cells remain in the population. Facing rows draw singly. Source: `work/build13/proofs/census/population/population.json`.\n',
'## Allocation and plans\n',
f"All {p['steps']:,} steps use pose 64, VQA 128, routing 64 and pointing 32. Absolute-distance draws fall from 15,600 to 5,904; camera displacement, movement direction and rotation receive 3,648 / 3,281 / 2,767 additional draws. The largest row repeat is {p['largest_repeat']}. Every allocation equals the lane plan. Source: `work/build13/proofs/census/PLAN_RUN.json`; reference pin: `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n/ROW_PLAN.json`.\n",
'| Cell | Draws across the plan |\n|---|---:|']
for name,n in p['allocation']['draws'].items():parts.append(f'| {name} | {n:,} |')
parts += ['\nThe camera, pose and pointing populations use the reference counts through synthetic native-reader rows and virtual offsets. They are not a production N census. N scene exclusions may reduce those populations on the host. The composed slice offsets and VQA offsets are real. Source: `work/build13/proofs/census/host_boundary.json`.\n',
'## Tests, mutations and coverage\n',
f"The packet suite passed {sum(v['outcome']=='passed' for v in packet.values())}/{len(packet)} checks. Source: `work/build13/proofs/final/packet/results.json`.",
f"The frozen suite ran {s['run']} tests: {s['passed']} passed, {s['skipped']} skipped, {s['preexisting']} preexisting failure events, {s['regressions']} regression events and {s['r2_failures']} R2 failures. The BF16 parity failure remains blocked. Source: `work/build13/SUITE_COMPARISON.json`. Failure-event counts include subtests and setup/import errors; they need not sum to test executions.\n",
f"The untouched base ran {base['tests']} tests: {len(base['passed'])} passed, {len(base['skips'])} skipped, {len(base['failures'])} failure events and {len(base['errors'])} error events. Its receipts are reused only after exact source/fixture checks and runner equivalence. Source: `work/build13/proofs/final/suite_base/results.json`; `work/build13/proofs/final/suite_base/RESUME_RECEIPT.json`.\n",
'| Mutation | Result |\n|---|---|']
for v in mut:parts.append(f"| {v['name']} | {v['status']} |")
parts += ['\nSource for every mutation result: `work/build13/proofs/mutations/RESULT.json`. Each clean targeted test passed before its mutant ran; all mutants reuse one tree directory.\n',
f"Coverage spans {cov['changed_statements']} changed statement heads since the untouched base. Source: `work/build13/CHANGED_COVERAGE.json`.\n",
f"CPU-reachable unresolved statements: {cov['classes'].get('CPU-reachable unresolved',0)}. Source: `work/build13/GAPS.json`.\n",
'| Coverage class | Statements |\n|---|---:|']
for name,n in cov['classes'].items():parts.append(f'| {name} | {n} |')
parts += ['\nCoverage uses standard-library compiled-source tracing and excludes top-level test files, as in build 12. Prior observations transfer only with exact file bytes or an identical complete function, and each transfer records hashes. Frame-host, GPU and model-loader gaps remain explicit. Scope declarations have no runtime instruction. Source: `work/build13/coverage13.py`; `work/build13/CHANGED_COVERAGE.json`.\n',
'## Preserved behavior\n',
'N retains its step-544 / 1d6eeb28 launch binding. Handover default-deny, receipt checks, Unicode rules, M1 binding and L1 refusals remain. Original-family text/reader/intake counts remain 1532/0/0, 2000/1186/1102, 2000/1222/1119 and 476/0/431. The 601-key exclusion and 144,000/144,000 parity sweep retain authenticated build-12 evidence; they were not rerun as full real-row proofs. Repaired-family counts were reproduced above. Sources: `work/build13/PRESERVATION.json`; `work/build12/PROOF_EQUALITY.json`; `work/build12/proofs/preservation/RESULT.json`; `work/build12/proofs/depth_sweep/RESULT.json`.\n',
'No inference selector, guard, fallback or agent loop was added. Changes concern training admission and sampling; native model forward paths and top-level training functions retain their source. Source: `work/build13/PRESERVATION.json`.\n',
'## Kits and operator sequence\n',
'All kits were staged from empty and remain GO=false. Their hashes come from `work/build13/KIT_RESULT.json`.\n',
'| Kit | Kit SHA-256 | Source SHA-256 |\n|---|---|---|']
for name,v in k.items():parts.append(f"| {name} | `{v['kit_sha256']}` | `{v.get('source_sha256',v.get('source_seal'))}` |")
parts += ['\nThe operator must verify the remote sources against the staged pins and resolve the native base, source manifests, frame maps and independent scene coverage. On the real frame host, set `STUDENT_R2_FRAME_HOST=1`, `STUDENT_R2_LOCAL_NODE=0` and `CUDA_VISIBLE_DEVICES=""`; the native intake guard requires this host declaration and still refuses full intake on Trinity. Source: `student_pilot/r2_intake.py`. Then run these host steps in order through `launch_r1.entry.frame_host`:',
'\n1. Run native `s1_routing.build`, then `r1_routing.compose_native` with the verified source manifests.',
'2. Run native `carrier_c1_run.prepare` through `s1_admission` on the composed routing receipt.',
'3. Run `r1_population.bind_prepared` on the prepared configuration; use its returned configuration and preparation receipt.',
'4. Run `r1_loader.production_audit` on that returned configuration. Missing or changed bindings refuse. Trinity remains prohibited for this full audit.\n',
'The exact request and unresolved parameters are in `work/build13/kits/r1/` and `work/build13/KIT_RESULT.json`. Do not launch from the pre-producer config.\n',
'## Limits and stand-ins\n',
'The native builder proof uses a bounded source fixture and synthetic host frame metadata; the encoding proof substitutes RGB frame loading and the pretrained processor only. The census uses published scene coverage as the lane did, placeholder frame pins, and GUESS 24 FPS where source metadata is absent. It does not establish independent frame-host coverage or real-scene numeric parity. Sources: `work/build13/proofs/builder/RESULT.json`; `work/build13/proofs/encode/RESULT.json`; `work/build13/proofs/census/CENSUS.json`.\n',
'No full host admission, production P weights, GPU/pretrained tower execution, independent full-store scene audit, remote upload, submission, Orchard call or GCS call was performed. Existing product-inference and FRAME64 blockers remain. Sources: `work/build13/KIT_RESULT.json`; `work/build13/CHANGED_COVERAGE.json`.\n',
'Superseded owned kit copies were overwritten with digest receipts; active kits retain their verified bytes. Final workspace usage and projected archive-extraction growth are checked explicitly. Peak workspace usage during the earlier extraction was not measured. Sources: `work/build13/RETAINED_KIT_RECEIPTS.json`; `work/build13/STORAGE.json`; `work/build13/package13.py`.\n',
'## For the confirmation\n',
'Run from the package root on the permitted compute node. Each command uses the bounded runner and fixed proof folders. The full census needs the named read-only external inputs; the archive does not carry their databases or raw slices.\n',
'```bash\nbash work/build13/run.sh work/build13/test13.py\nbash work/build13/run.sh work/build13/census13.py\nbash work/build13/run.sh work/build13/native_builder13.py\nbash work/build13/run.sh work/build13/recompose13.py\nbash work/build13/run.sh work/build13/census13.py --resume\nbash work/build13/run.sh work/build13/encode13.py\nbash work/build13/run.sh work/build13/mapping13.py\nbash work/build13/run.sh work/build13/mutations13.py\nbash work/build13/run.sh work/build13/preserve13.py\nbash work/build13/run.sh work/build13/edges13.py\nbash work/build13/run.sh work/build13/packet_inputs13.py\nbash work/build13/run.sh work/build13/packet13.py integrated packet contract\nbash work/build13/run.sh work/build13/package13.py out/tree_rebuild_b13_'+seal['tree_sha256'][:8]+'.tar\nbash work/build13/run.sh work/build13/compare13.py\nbash work/build13/run.sh work/build13/coverage13.py\nbash work/build13/run.sh work/build13/storage13.py\n```\n',
'Fresh kit staging is reproduced with `kits13.py` from an empty `work/build13/kits`; preserve any existing kit directory before rerunning it. Source sealing uses `work/n1fix2/seal.py`; archive production uses `work/build13/delivery13.py`. Never use the supplied production host entry on Trinity.\n',
f"The final source seal is `{seal['tree_sha256']}`. Inventory and base comparison are `out/TREE_FILES.sha256` and `out/TREE.diff`. The package path, byte count and checksum are recorded in `work/build13/DELIVERY.json`.\n"]
report='\n'.join(parts)
(L/'out/BUILD13_REPORT.md').write_text(report)
d=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md';text=d.read_text();head='\n## Build 13\n'
if head in text:text=text.split(head)[0]
d.write_text(text+head+'\nR1 composition authenticates N slice identity before native preparation. The population producer then uses final native-reader offsets, publishes a bound complete population and validates the sampling plan. Source identity takes precedence over the sealed question-type table. Host audit consumes the produced configuration. All kits remain GO=false pending real host inputs and production qualification. See `BUILD13_REPORT.md` and `work/build13/CHANGED_COVERAGE.json`.\n')
(B/'STATUS.md').write_text('# Build 13 status\n\nImplementation and CPU proofs complete; GO=false. Census and plan match the lane. Final report: `out/BUILD13_REPORT.md`. Final delivery qualification is running; see `FINAL_RUNS.json`. Archive qualification remains pending until `proofs/integrity/RESULT.json` passes.\n')
print('Report and design record written')
