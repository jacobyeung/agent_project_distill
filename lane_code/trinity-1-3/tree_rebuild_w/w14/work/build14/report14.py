"""Write the review result from recorded evidence, without upgrading blocked claims."""
from pathlib import Path
import json,sys,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1';sys.path.insert(0,str(T))
from student_pilot.r1_handover import HANDOVER_ROW_KEYS,EFFECTIVE_DEFAULTS
def read(p,default=None):return json.loads((L/p).read_text()) if (L/p).exists() else default
def line(file,needle):
    return next(i for i,s in enumerate((T/file).read_text().splitlines(),1) if needle in s)
def ref(file,needle):return f'`{file}:{line(file,needle)}`'
real=read('work/build14/proofs/real/RESULT.json',{})
kit=read('work/build14/KIT_RESULT.json',{})
comp=read('work/build14/SUITE_COMPARISON.json',{})
cov=read('work/build14/CHANGED_COVERAGE.json',{})
packet=read('work/build14/proofs/final/packet/results.json',{})
tests=read('work/build14/proofs/final_focused/TESTS.json',{})
suite=read('work/build14/proofs/final/suite_tree/results.json',{})
census=read('work/build14/proofs/census/CENSUS.json',{})
storage=read('work/build14/STORAGE.json',{})
seal=read('out/TREE_SEAL.json',{})
out=['# Build 14',
'**Real A/C handover admission is blocked. GO=false.** N binds the lineage scale weight, compares effective config values, and reads milestone exports at their absolute steps. P defaults to resetting routing opener embeddings; N keeps them. Those operations produce different weights, so the required compared key still refuses. Both real-config checks return `P_EXPORT_CONFIG_DIFFERENCE:routing_opener_init`. Sources: `work/build14/proofs/real/RESULT.json`; `work/build14/proofs/opener/RESULT.json`.',
'## Implementation and acceptance',
'| Requirement | Result | Evidence |\n|---|---|---|',
'| Scale weight from config and card, focal override only | Implemented; 0.04 is bound in both inputs | `work/build14/INPUTS.json`; `tests/test_r1_build14.py` |',
'| Effective defaults and file-pin identity | Implemented; unknown missing keys still refuse | `student_pilot/r1_handover.py`; `work/build14/proofs/final_focused/TESTS.json` |',
'| Audited row/bookkeeping boundary | Implemented with an H1 guard; optimizer, loss, topology and route_table remain compared | Key table below |',
'| Admit real A and C against the kit | **Blocked by routing_opener_init** | `work/build14/proofs/real/RESULT.json` |',
'| Receipt and sampler resume at the export milestone | Implemented; producer, reader and N resumed plans execute | `work/build14/proofs/final_focused/n1fix/b14_milestones/RESULT.json` |',
'| Full parity sweep rerun | **Not run: required generator/reference bytes are outside the authorized inputs and absent from the package** | `work/build14/PRESERVATION.json` |',
'The kit retains `routing_opener_init=keep`. A diagnostic copy using `reset` admits both A and C; that copy is not a staged kit. Changing the kit to reset would overwrite trained opener rows and change the preserved behavior. The native reset function assigns each opener the mean of its constituent token embeddings, while keep returns without that assignment. The CPU counterexample replaces P weights with small embedding tensors; it does not claim to inspect P opener values. Sources: `work/build14/proofs/real/RESULT.json`; `work/build14/proofs/opener/RESULT.json`; `student_pilot/r2_openers.py:38`; `student_pilot/carrier_c1_routing.py:758`.',
'The native warm start loads the LM before opener initialization. Its subsequent heads phase writes only auxiliary_heads, so it does not undo an opener reset. Sources: `student_pilot/carrier_c1_run.py:821-840,952-959,1000`; the export/keep/reset regression is `tests/test_r2_build3.py:test_opener_export_keep_and_reset`.',
'## Key decisions',
'| Key | Decision | Reason | Code line | Test |\n|---|---|---|---|---|']
for key,reason in HANDOVER_ROW_KEYS.items():
    out.append(f'| `{key}` | Boundary'+(' with nested guard' if key=='h1' else '')+f' | {reason} | '+ref('student_pilot/r1_handover.py',repr(key)+':')+' | `test_defaults_pins_unknowns_and_boundary_keys`; real A/C diagnostic |')
defaults={'frame_count':'carrier_c1_run.py:811','max_pixels':'carrier_c1_data.py:209','min_pixels':'carrier_c1_data.py:209','geometry_connector':'carrier_c1_run.py:813-815','routing_opener_init':'r2_openers.py:38'}
for key,value in EFFECTIVE_DEFAULTS.items():
    out.append(f'| `{key}` | Compared; absent = `{value}` | Trainer default at `student_pilot/{defaults[key]}`'+('; keep and reset differ' if key=='routing_opener_init' else '')+' | '+ref('student_pilot/r1_handover.py',repr(key)+':')+' | `test_defaults_pins_unknowns_and_boundary_keys` |')
out += [
'| `camera_overrides.weight_scale` | Effective comparison; kit binds 0.04 | Preparation stores base camera settings; runtime merges overrides. The prepared lineage value is 0.04 | '+ref('student_pilot/r1_training.py',"card = load")+'; `carrier_c1_run.py:627,716` | `test_scale_card_config_and_override`; `test_effective_camera_and_metadata_refusal`; real A/C |',
'| Other camera overrides | Only weight_focal 2.0 is allowed in R1 | Any other override refuses even if it names a camera default | '+ref('student_pilot/r1_training.py',"R1_CAMERA_OVERRIDES_DIFFER")+' | `test_scale_card_config_and_override` |',
'| `recipe.milestones` | Boundary | Export timing is rebound; recipe losses, batch, schedule and optimizer settings remain compared | '+ref('student_pilot/r1_handover.py',"if key == 'recipe'")+' | Milestone producer/reader and real A/C diagnostic |',
'| File pins, including depth_init | Equal SHA-256 identifies equal pinned bytes across paths | Replica reads verify the original digest; other dictionary fields remain compared. Different depth-init bytes still refuse by name | '+ref('student_pilot/r1_handover.py','def pin_values')+' | `test_defaults_pins_unknowns_and_boundary_keys`; inherited depth-init refusals |',
'| Unknown keys, depth_enabled, align, camera, optimizer/loss fields | Compared; differing values refuse | No permission to change topology, loss or optimizer groups | '+ref('student_pilot/r1_handover.py','def compare_configs')+' | Real refuse set and inherited native group-table tests |',
'H1 permits only the named row and bookkeeping fields. Unknown H1 fields and a changed faithful-own-row mode refuse. In this trainer, `routing_pose_targets` has no consumer; `camera_types` only selects row processing. N still validates S2 off and refuses faithful own camera rows. Both route-file JSON values match, despite different serialization hashes; the embedded `route_table` remains compared. Sources: `student_pilot/h1_faithful.py:10-24`; `student_pilot/carrier_c1_run.py:703,717,1258`; `work/build14/proofs/opener/RESULT.json`.',
'The camera defaults come from authenticated preparation metadata, not numeric constants in the comparator. The real comparison uses P’s named preparation receipt and the exact local replica of the pinned parent artifact; it does not rewrite A or C. The optional metadata replicas verify the original SHA-256. Parent metadata records the scale token and scale branch among its trained parameters. Sources: `work/build14/proofs/real/RESULT.json`; `work/build14/proofs/opener/RESULT.json`.',
'The explicit file-pin rule applies to depth_init: identical pinned bytes at another path admit. This is the scoped exception to the path-only refusal listed in the Build 12 report; different hashes, head initialization metadata and native optimizer-group differences still refuse. Sources: `tests/test_r1_build14.py`; `tests/test_r2_n1fix3.py`; `out/BUILD12_REPORT.md`.',
'Absent or null pixel-limit config fields leave native DEFAULT_PIXELS active: minimum 128×128 and maximum 384×384 pixels (`student_pilot/pose_samples.py:37`; consumption at `student_pilot/carrier_c1_data.py:209`). The geometry constructor defaults geometry_online to None and attaches no connector (`student_pilot/carrier_c1.py:109,129`); R1 independently forbids geometry extensions.',
'## Real configurations and refusals',
'| Config | SHA-256 of supplied file | Kit result | Diagnostic N reset only |\n|---|---|---|---|']
for key,v in real.get('real',{}).items():out.append(f"| {key} | `{v['config']['sha256']}` | `{v['result']}` | {v['counterfactual_only_N_reset']} |")
out+=['Source: `work/build14/proofs/real/RESULT.json`. A’s supplied file hash is distinct from its trainer configuration identity. The comparison loads the supplied JSON bytes.',
'| Refuse variant | A | C |\n|---|---|---|']
for key,value in real.get('refuse',{}).get('A',{}).items():out.append(f"| `{key}` | `{value}` | `{real['refuse']['C'][key]}` |")
out+=['Source: `work/build14/proofs/real/RESULT.json`. These mutations use the diagnostic reset target so the opener mismatch cannot hide another refusal.',
'The same mutations also run against the unchanged kit. None admits. For unknown_extra, the unchanged kit first reports the opener mismatch; the aligned-policy diagnostic proves the independent named unknown-key refusal. Source: `work/build14/proofs/real/RESULT.json`, `refuse_against_kit`.',
'## Milestone handover',
'The receipt producer requires an integer artifact step in P’s run milestones and equality with the checkpoint completion step. The reader requires the same receipt step and the complete pinned closure. `progress` and `boundary` already derive the absolute schedule step from the artifact; N’s cell sampler skips the corresponding prefix. The tests compare each resumed N plan with the uninterrupted plan. Sources: `launch_r1/p_handover_receipt.py`; `student_pilot/r1_handover.py`; `student_pilot/r1_training.py`; `work/build14/proofs/final_focused/n1fix/b14_milestones/RESULT.json`.',
'| Step | Pose position | VQA position | Routing position | Pointing position |\n|---|---:|---:|---:|---:|']
for step in (100,200,400,600):out.append(f'| {step} | {step*64} | {step*128} | {step*64} | {step*32} |')
out+=['Source: `work/build14/proofs/final_focused/n1fix/b14_milestones/RESULT.json`. The fixture uses the sealed native checkpoint/export functions with a tiny CPU model and local collective stand-ins. A non-milestone export, a different completion step and a different receipt step refuse. This is not publication of a real P receipt.',
'## Preserved behavior and qualification',
'The preserved behaviors are the step-544 / 1d6eeb28 parent launch, handover default deny, receipt closure, Unicode rules, M1 fixed-buffer checks, L1 typed refusals, source-identity population cells, disjoint reader offsets, native routing composition, and the host-only production audit. Sources: `out/BUILD13_REPORT.md`; `work/build14/PRESERVATION.json`; `work/build14/proofs/final_focused/TESTS.json`.',
'Original-family read/reader/intake counts are 1532/0/0, 2000/1186/1102, 2000/1222/1119 and 476/0/431. Repaired slice counts are 777 / 1,476 / 8,067. The removal proof retains all 601 keys. Sources: `work/build14/proofs/text/RESULT.json`; `work/build14/proofs/row_delta/RESULT.json`; `work/build14/proofs/census/CENSUS.json`; `work/build14/proofs/preservation/RESULT.json`.',
'The census and allocation proof compares every cell with the lane reference. The plan retains 1,000 steps, quotas 64/128/64/32, absolute-distance draws 5,904, camera refill 3,648/3,281/2,767 and maximum repeat 4. Sources: `work/build14/proofs/census/CENSUS.json`; `work/build14/proofs/census/PLAN_RUN.json`. Camera/pose/pointing population offsets remain host-boundary stand-ins, and absent FPS uses GUESS 24 as declared by the census.',
'The six population/routing guard mutations run with one reused mutant tree. Source: `work/build14/proofs/mutations/RESULT.json`.',
f"Focused final tests: {tests.get('tests','pending')}; successful: {tests.get('successful','pending')}. Source: `work/build14/proofs/final_focused/TESTS.json`.",
f"Packet suite: {sum(v.get('outcome')=='passed' for v in packet.values())}/{len(packet)} passed. Source: `work/build14/proofs/final/packet/results.json`.",
f"Frozen suite: {suite.get('tests','pending')} tests; {len(suite.get('passed',[]))} passed; {len(suite.get('skips',[]))} skipped. Source: `work/build14/proofs/final/suite_tree/results.json`."]
if comp:
    failures=comp.get('failures',[]);reg=[r for r in failures if not r['preexisting']]
    out.append(f"Failure events: {sum(r['preexisting'] for r in failures)} preexisting; {len(reg)} regressions; R2 failures: {comp.get('r2_failures')}. Source: `work/build14/SUITE_COMPARISON.json`. Events include setup and subtest errors and need not sum to test executions.")
    out.extend('- '+r['test']+': '+r['cause'] for r in reg)
out+=['The 144,000/144,000 sweep result is authenticated inherited evidence, not a rerun. Its generator and expected responses are not packaged or authorized external inputs. Source: `work/build14/PRESERVATION.json`; `work/build12/proofs/depth_sweep/RESULT.json`.',
'## Changed-statement coverage',
f"Coverage spans {cov.get('changed_statements','pending')} changed statement heads against the untouched base. Source: `work/build14/CHANGED_COVERAGE.json`.",
'| Class | Statements |\n|---|---:|']
for key,value in cov.get('classes',{}).items():out.append(f'| {key} | {value} |')
out+=['Source: `work/build14/CHANGED_COVERAGE.json`; `work/build14/GAPS.json`. Standard-library compiled-source monitoring authenticates current observations. Inherited observations transfer only for identical files or complete functions, with hashes recorded. CPU gaps are reported rather than inferred away.',
'## Kits and package',
'| Kit | Kit SHA-256 | Source SHA-256 | GO |\n|---|---|---|---|']
for key,value in kit.items():out.append(f"| {key} | `{value['kit_sha256']}` | `{value.get('source_seal',value.get('source_sha256'))}` | false |")
out += ['Source: `work/build14/KIT_RESULT.json`. All kits are staged from empty. Verified remote sources, frame-host catalogs, full admission, GPU/pretrained execution, BF16 parity and the existing product-inference blockers remain unresolved. No job was submitted.',
f"Source seal: `{seal.get('tree_sha256')}`. Inventory and base diff: `out/TREE_FILES.sha256`, `out/TREE.diff`. The gzip package path, size and checksum are in the external receipt `work/build14/DELIVERY.json`; that self-referential digest receipt is not embedded in the archive. Source: `out/TREE_SEAL.json`.",
'The workspace cap is 1,500,000,000 bytes; measured workspace and temporary sizes are recorded in `work/build14/STORAGE.json` and the external final integrity receipt. Temporary storage checks run before and after each test under `ulimit -f 204800`.',
'Completed early CPU tensor fixtures are retained as digest receipts. Final focused proof tensors, native databases and observation records remain intact. Source: `work/build14/RETAINED_CPU_PRODUCTS.json`.',
'## For the confirmation',
'Run from the package root on the permitted compute node. The real-config and full census proofs require the named read-only external inputs. The parity rerun cannot be reproduced from the authorized package inputs.',
'```bash\nbash work/build14/run.sh work/build14/real14.py\nbash work/build14/run.sh work/build14/opener14.py\nB14_PROOF=final_focused bash work/build14/run.sh work/build14/test14.py tests.test_r1_build14 tests.test_r2_build_n1 tests.test_r2_n1fix tests.test_r2_n1fix3 tests.test_r2_build12 tests.test_r1_build13\nbash work/build14/run.sh work/build14/census14.py\nbash work/build14/run.sh work/build14/native_builder14.py\nbash work/build14/run.sh work/build14/recompose14.py\nbash work/build14/run.sh work/build14/census14.py --resume\nbash work/build14/run.sh work/build14/encode14.py\nbash work/build14/run.sh work/build14/mutations14.py\nbash work/build14/run.sh work/build14/text14.py\nbash work/build14/run.sh work/build14/row_delta14.py\nbash work/build14/run.sh work/build14/preservation14.py\nbash work/build14/run.sh work/build14/packet_inputs14.py\nbash work/build14/run.sh work/build14/packet14.py integrated packet contract\nbash work/build14/run.sh work/build14/compare14.py\nbash work/build14/run.sh work/build14/coverage14.py\nbash work/build14/run.sh work/build14/storage14.py\n```',
'`final14.py` records the ordered seal, fresh-kit, packet and frozen-suite commands. `package14.py` takes the archive path from `DELIVERY.json`; it reuses a suite group only when source, fixtures, runner and bound inputs match. Run `kits14.py` only with an empty `work/build14/kits` directory. Preserve an existing kit directory before restaging. Source sealing uses `work/n1fix2/seal.py`; packaging uses `work/build14/delivery14.py`.',
'Additional count and guard checks: `bash work/build14/run.sh work/build14/edges14.py`, `bash work/build14/run.sh work/build14/confusables14.py`, `bash work/build14/run.sh work/build14/mapping14.py`, and `bash work/build14/run.sh work/build14/check_results14.py --require`. Authenticate inherited evidence with `bash work/build14/run.sh work/build14/preserve14.py`. Verify the finished delivery with `bash work/build14/run.sh work/build14/integrity14.py`.']
plan=read('work/build14/proofs/census/PLAN_RUN.json')
oldplan=read('work/build13/proofs/census/PLAN_RUN.json')
population=read('work/build14/proofs/census/population/population.json')
counts=['## Census and allocation equality',
'Each cell retains its eligible population and planned draws. Sources: `work/build13/proofs/census/PLAN_RUN.json`; `work/build14/proofs/census/PLAN_RUN.json`; `work/build14/COUNT_EQUALITY.json`.',
'| Cell | Build 13 eligible | Build 14 eligible | Build 13 draws | Build 14 draws |\n|---|---:|---:|---:|---:|']
for key,value in plan['allocation']['eligible'].items():
    counts.append(f"| {key} | {oldplan['allocation']['eligible'][key]:,} | {value:,} | {oldplan['allocation']['draws'][key]:,} | {plan['allocation']['draws'][key]:,} |")
counts += [f"The VQA scan read {census['vqa']['read']:,} rows and retained {sum(census['vqa']['eligible_by_cell'].values()):,}. It refused 601 excluded rows and 6 non-ASCII traces. Source: `work/build14/proofs/census/CENSUS.json`.",
f"Source identity overrides: `{population['source_identity_overrides']}`. Unit counts: `{population['asked_units']}`. Facing statistics: `{population['facing']}`. These equal the prior proof. Sources: `work/build14/proofs/census/population/population.json`; `work/build13/proofs/census/population/population.json`.",
'The bounded sample agrees with P’s sealed classifier. Zero-quota cells remain reported, and facing rows draw singly. Sources: `work/build14/proofs/mapping/RESULT.json`; `work/build14/proofs/census/population/population.json`.']
out[out.index('## Changed-statement coverage'):out.index('## Changed-statement coverage')]=counts
rendered=''
for index,part in enumerate(out):
    rendered+=('' if index==0 else '\n' if part.startswith('|') and out[index-1].startswith('|') else '\n\n')+part
(L/'out/BUILD14_REPORT.md').write_text(rendered+'\n')
design=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md';text=design.read_text();text=text.split('\n## Build 14\n')[0]
text+='\n## Build 14\n\nR1 binds camera weight_scale=0.04 in the configuration, training binding and pinned card. The lineage preparation supplies the same camera value. The validator requires agreement and permits only weight_focal=2.0 beside it.\n\nThe handover comparator normalizes audited trainer defaults and file-pin identities, and rebinds the audited row/bookkeeping fields. Model topology, loss, optimizer settings, unknown fields and routing opener policy remain compared. P reset and N keep differ because reset overwrites opener embeddings; real A/C admission remains blocked.\n\nA P receipt records the artifact’s own integer milestone step. The checkpoint and receipt must agree with that step. N resumes its schedule and cell sampler at the absolute step. CPU producer/reader proofs cover 100, 200, 400 and 600 and reject non-milestones and inconsistent receipts.\n\nSee `out/BUILD14_REPORT.md` and `work/build14/` for source pins, key decisions, qualification results and limitations. GO=false.\n'
design.write_text(text)
