"""Render the review packet from measured receipts; missing proofs remain explicit."""
import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build_n1';O=L/'out'
def read(path,default=None):
    path=L/path
    return json.loads(path.read_text()) if path.exists() else default
def source(path):return '`'+path+'`'
def table(headers,rows):
    def cell(x):return str(x).replace('|','\\|').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n|'+ '|'.join('---' for _ in headers)+'|\n'+''.join('| '+' | '.join(cell(x) for x in row)+' |\n' for row in rows)
bindings=read('work/build_n1/BINDING_TABLE.json',[])
kit=read('work/build_n1/KIT_RESULT.json',{})
delivery=read('work/build_n1/DELIVERY.json',{})
seal=read('out/TREE_SEAL.json',{})
if delivery.get('tree_seal') != seal.get('tree_sha256'):delivery={}
inputs=read('work/build_n1/INPUT_BINDINGS.json',{})
mix=read('work/build_n1/inputs/mix.json',{})
audit=read('work/build_n1/proofs/loader_audit/RESULT.json',{})
coverage=read('work/build_n1/N1_CHANGED_COVERAGE.json',{})
comparison=read('work/build_n1/SUITE_COMPARISON.json',{})
packet=read('work/build_n1/proofs/packet/results.json',{})
targeted=read('work/build_n1/proofs/targeted/results.json',{})
contracts=read('work/build_n1/proofs/contracts/results.json',{})
inventory=read('work/build_n1/proofs/audit/INFERENCE_COMPONENTS.json',{})
blockers=read('work/build_n1/CARRIED_BLOCKERS.json',{})
finished=(B/'FINAL_PASS.json').exists()
report=(B/'BINDING_TABLE.md').read_text()
report+='\n## R1 kit result\n\n'
report+='The R1 kit is staged with **GO=false**. It is not launch-ready. The source changes, input contracts and bounded CPU proofs are available for review. Full frame-host admission and independent legality review remain unproven. No job was submitted.\n\n'
report+='The binding table comes from `work/build_n1/BINDING_TABLE.json` and preserves the complete registry. GF-1-only requirements remain named blockers of A2. The deployed selector, box policy, room policy, alias table and depth cut remain native-evaluation requirements; the orchestrator must approve their launch scope.\n\n'
report+='## Closed implementation and input bindings\n\n'
report+='- The prescribed parent metadata and H1 archive inventory are bound. The parent starts the new schedule at step 0. An R1 export uses the native carrier artifact format and preserves its absolute schedule and per-stream sampler positions. Configuration, store, row-plan and export-receipt mismatches refuse. Source: `work/build_n1/INPUT_BINDINGS.json`, `work/tree_r1/student_pilot/r1_training.py`, `work/build_n1/proofs/targeted/r1/export/RESULT.json`.\n'
report+='- The default VQA receipt selects v7 because its merge validator reports PASS without appended failures. This is a receipt binding, not proof of full-store eligibility or remote deployment. Switching between v6 and v7 uses one receipt parameter and derives the VQA store identity from it. Sources: `work/build_n1/inputs/v7_validator.json`, `work/build_n1/inputs/store_parameter.json`, `work/build_n1/proofs/targeted/results.json`.\n'
report+='- S2 is OFF, own-response probability is 0, own-valued input rows refuse, and the connector is absent. The config fixes 32 frames, duplicate layout, markers, world 4, 288 rows per step, a 1,000-step recipe, milestones 100/200/400/600/800/1000 and a separate stop-after parameter. Source: `work/build_n1/inputs/config.json`.\n'
report+='- The config keeps the scale loss on at weight 1.0 (GUESS for the actual D0 runtime weight; the prior kit supplied this choice). Actual D0 scale settings remain a named blocker. The existing native trainer records each pose microstep’s `pose_parts`, including scale, in its per-step metrics. An entirely missing scale branch retains the seeded native constructor tensors; a partially present branch refuses. Sources: `work/build_n1/inputs/config.json`, `work/tree_r1/student_pilot/carrier_c1_run.py:1585`, `work/build_n1/proofs/targeted/r1/scale_load/RESULT.json`. Real pretrained initialization and real training logs were not checked.\n'
report+='- Export continuation restarts optimizer moments because the stipulated artifact is an inference export. The absolute LR schedule and row plan continue. A real P export and its boundary receipt remain missing. Sources: `work/build_n1/DECISIONS.md`, `work/tree_r1/student_pilot/r1_training.py:start`.\n\n'
report+=table(['Binding','Value','Source'],[
 ['Init artifact SHA',inputs.get('init',{}).get('artifact_sha256'),'work/build_n1/INPUT_BINDINGS.json'],
 ['Init remote metadata',inputs.get('init',{}).get('location'),'work/build_n1/INPUT_BINDINGS.json'],
 ['Init remote archive',inputs.get('init',{}).get('archive',{}).get('parts'),'work/build_n1/INPUT_BINDINGS.json'],
 ['VQA declared rows',inputs.get('store',{}).get('count'),'work/build_n1/inputs/v7_receipt.json'],
 ['VQA database SHA',inputs.get('store',{}).get('database',{}).get('sha256'),'work/build_n1/inputs/v7_receipt.json'],
 ['VQA receipt SHA',inputs.get('store',{}).get('receipt',{}).get('sha256'),'work/build_n1/INPUT_BINDINGS.json'],
 ['Mix SHA',inputs.get('mix',{}).get('sha256'),'work/build_n1/INPUT_BINDINGS.json']])
report+='\n## Mix and eligible populations\n\n'
report+='The pinned vehicle-N card is `work/build_n1/inputs/R1_CARD_v2.md`; the derived config is `out/MIX_A0.json`, identical to `work/build_n1/inputs/mix.json`. Size and room start at 0; their released slots go to direction. Camera-object absolute distance is excluded explicitly. The 581 room programs remain outside routing, as required by the user brief and the room-program admission refusal; their source count is documented in `work/design/NEXT_LEG_INIT_RULE_20261116.md`. The existing recovery and unit refusals remain active. Sources: the pinned card, `work/build_n1/DECISIONS.md`, `work/tree_r1/student_pilot/r1_training.py:row_check`, `work/tree_r1/student_pilot/routing_requirements.py`.\n\n'
report+='Each cell is capped at four draws per eligible row over the complete schedule. The allocator reports cuts and refuses a stream whose remaining capacity cannot fill its quota. The following numbers are requested rates, not admitted populations. Full post-filter counts, numerical ceilings and actual repeats remain UNKNOWN; no sample count is extrapolated. Sources: `work/tree_r1/student_pilot/r1_mix.py`, `work/build_n1/proofs/loader_audit/RESULT.json`.\n\n'
report+=table(['Stream','Cell','Requested rows/step','Eligible / ceiling / actual repeats','Source'],[
 [c['stream'],c['type'],c['rows_per_step'],'UNKNOWN' if c['rows_per_step'] else 'excluded / 0 / 0','work/build_n1/inputs/mix.json'] for c in mix.get('cells',[])])
report+='\n## Production-loader audit\n\n'
report+='**BLOCKED.** The proof reads bounded source slices with the real native `Rows.row` function and the R1 admission checks. It retains counts, hashes and five accepted trace examples per sampled family where available. It does not run RGB preparation or replace RGB, heads, towers, scene coverage or the model with stand-ins. Sources: `work/build_n1/loader_audit.py`, `work/build_n1/proofs/loader_audit/RESULT.json`; trace files are beside that result.\n\n'
report+=table(['Sample family','Rows read','Native reader result','Post-filter eligible','Source'],[
 [name,value.get('counts',{}).get('read'),json.dumps(value.get('native_reader',{}),sort_keys=True),'UNKNOWN',
  'work/build_n1/proofs/loader_audit/'+name+'.json'] for name,value in audit.get('families',{}).items()])
report+='\nRoom-v2 and the VQA merge describe different producer revisions. Their counts cannot be combined into a launch population. One-line room rows refuse, and room remains excluded until a full admitted population exists. Sources: `work/build_n1/inputs/room_v2_CHECK.json`, `work/build_n1/inputs/v7_validator.json`, `work/build_n1/proofs/loader_audit/room_v2.json`.\n\n'
report+='The production audit entry enumerates the final native sampler, checks actual repetitions and reports family shares, question-unit and printed-status marginals, plus recovery/unit counts consumed by launch admission. It refuses local full-store execution. This full audit has not run; the missing inputs are complete scene-admitted stores, their post-filter index maps and real frame-host preparation. Source: `work/tree_r1/student_pilot/r1_loader.py:production_audit`.\n\n'
report+='## CPU proof and test outcomes\n\n'
rows=[]
for name,data,path in [('Targeted R1',targeted,'work/build_n1/proofs/targeted/results.json'),('Registry and kit',contracts,'work/build_n1/proofs/contracts/results.json')]:
 rows.append([name,data.get('tests','PENDING'),len(data.get('passed',[])),0,len(data.get('failures',[]))+len(data.get('errors',[])),len(data.get('failures',[]))+len(data.get('errors',[])),path])
rows.append(['Contract packet',len(packet),sum(v.get('outcome')=='passed' for v in packet.values()),0,
             sum(v.get('outcome')!='passed' for v in packet.values()),'packet contract suite','work/build_n1/proofs/packet/results.json'])
rows.append(['Frozen full tree',*[comparison.get(k,'PENDING') for k in ('run','passed','preexisting','regressions','r2_failures')], 'work/build_n1/SUITE_COMPARISON.json'])
report+=table(['Suite','Run','Passed','Pre-existing failure events','Regression events','R2 failures','Source'],rows)
report+='\nFailure-event counts can include subtests and setup errors; they are not disjoint method counts. The frozen comparison preserves inherited BF16-cache parity failures as explicit A2 blockers and does not relabel them as passes. Only exact input-hash matches resume suite groups. Sources: `work/build_n1/SUITE_COMPARISON.json`, `work/build_n1/proofs/suite_tree/*/GROUP_RECEIPT.json`, `work/build_n1/proofs/suite_base/*/GROUP_RECEIPT.json`.\n\n'
report+='The export proof uses a seeded tiny native model instead of the pretrained GPU model; local stand-ins cover FSDP publication and rank/barrier collectives. Native export, artifact parsing, tensor loading, progress checks, LR calculation and the sampler run as production functions. The room proof uses the real native reader with a synthetic text fixture. Real-row proofs use unmodified source text. Sources: `work/tree_r1/tests/test_r2_build_n1.py`, `work/build_n1/proofs/targeted/r1/export/RESULT.json`, `work/build_n1/proofs/loader_audit/RESULT.json`.\n\n'
report+='## Changed-statement coverage\n\n'
report+='Coverage uses standard-library `sys.monitoring`, compiled-code fingerprints and exact file hashes. Changed AST statement heads are compared against the authenticated inherited package. Uncovered lines remain uncovered. Source: `work/build_n1/N1_CHANGED_COVERAGE.json`.\n\n'
report+=table(['Class','Statements','Source'],[[k,v,'work/build_n1/N1_CHANGED_COVERAGE.json'] for k,v in coverage.get('classes',{'PENDING':'PENDING'}).items()])
report+='\nThe base-relative coverage inventory remains in `work/build_n1/CHANGED_COVERAGE.json`. CPU-reachable gaps, frame-host branches and GPU/model-loader branches are not production qualification.\n\n'
report+='## Package and frame-host packet\n\n'
report+=table(['Artifact','Value','Source'],[
 ['Tree seal',seal.get('tree_sha256'),'out/TREE_SEAL.json'],['Source inventory','out/TREE_FILES.sha256','out/TREE_SEAL.json'],
 ['Source diff','out/TREE.diff','out/TREE_SEAL.json'],['Package',delivery.get('path','PENDING'),'work/build_n1/DELIVERY.json'],
 ['Package bytes',delivery.get('bytes','PENDING'),'work/build_n1/DELIVERY.json'],['Package SHA',delivery.get('sha256','PENDING'),'work/build_n1/DELIVERY.json'],
 ['Kit','work/build_n1/kits/r1','work/build_n1/KIT_RESULT.json'],['Kit SHA',kit.get('kit_sha256'),'work/build_n1/KIT_RESULT.json'],
 ['Kit config SHA',kit.get('config_sha256'),'work/build_n1/KIT_RESULT.json'],['Host packet','work/build_n1/kits/r1/k/h.json','work/build_n1/KIT_RESULT.json'],
 ['Host packet SHA',kit.get('frame_host_sha256'),'work/build_n1/KIT_RESULT.json'],['Unresolved staging entries',kit.get('unresolved'),'work/build_n1/KIT_RESULT.json']])
report+='\nThe kit was produced from an empty directory. Its CPU entry is `work/build_n1/kits/r1/b/f.sh`; its request requires the disk plan, regenerated routing selection, empty root, runtime binaries and directory modes. The local refusal proof covers an empty root and missing staging/selection inputs. It does not prove camera, pose or pointing metadata on real frames. The complete sandbox/staging namespace, real binaries, reviewed selection pin and host receipt remain missing. Sources: `work/tree_r1/launch_r1/entry.py`, `work/build_n1/kits/r1/k/h.json`, `work/build_n1/proofs/targeted/r1/host/empty_validated/receipt.json`.\n\n'
report+='## Blockers carried forward\n\n'
report+='The launch-binding rows at the start remain blocked except the parent-selection and metadata-location binding. No requested evidence record was accepted without its missing proof. Gap records use an explicit non-accepting schema and are not substituted into the registry. Source: `work/build_n1/CARRIED_BLOCKERS.json`, `work/build_n1/inputs/EVIDENCE_*.json`.\n\n'
report+=table(['Additional blocker','Missing input','Source'],[[v['name'],v['missing'],'work/build_n1/CARRIED_BLOCKERS.json'] for v in blockers.get('additional',[])])
report+='\nThe actual D0 processor min/max resolution values remain missing. The full input inventory and independent canonical-scene/alias coverage remain missing. Every sealed benchmark and held-out dev exclusion stays active; unknown overlap does not count as clean. Sources: `work/build_n1/BINDING_TABLE.json`, `work/build_n1/inputs/config.json`.\n\n'
report+='## For the review\n\n'
report+='One independent review is requested for the changed admission and legality inputs: the R1 training-only evidence scope; parent selection and P-export progress contract; receipt-selected VQA store; recovery/room source revision mismatch; room and own-row refusals; size, room and camera-object-distance exclusions; capped mix allocation and no-substitution reader behavior; absent-scale initialization; all-stream exclusion coverage; processor pin; remote staging closure; and real frame-host assertions. The policy records remain intact for native evaluation. The local RESULT event requests this single review; it was not sent externally. Sources: `out/RESULT_build_n1.json`, `work/build_n1/DECISIONS.md`, `work/build_n1/CARRIED_BLOCKERS.json`.\n\n'
report+='## Product inference outside registered weights\n\n'
report+='This build changes training and input admission. It does not repair or certify the product inference path. The following confirmed operations remain outside registered weights; lane b03_e2etest must judge them. Source: `work/build_n1/proofs/audit/INFERENCE_COMPONENTS.json`.\n\n'
report+=table(['File:line','Component','Operation'],[[r['file']+':'+str(r['line']),r['component'],r['operation']] for r in inventory.get('known_outside_forward',[])])
report+='\nThe complete conservative static import-closure inventory follows. It includes orchestration, preprocessing, tables, validators and forward wrappers; inclusion does not prove that a component executes on every answer. Dynamic completeness and actual RGB-to-answer execution were not checked. The exact hashes and import edges are in `work/build_n1/proofs/audit/INFERENCE_COMPONENTS.json`. No existing selector, policy or fallback was changed for product acceptance.\n\n'
report+='<details>\n<summary>Complete static component inventory with file and line</summary>\n\n'
report+=table(['File:line','Component','Classification'],[[r['file']+':'+str(r['line']),r['component'],r['classification']] for r in inventory.get('components',[])])
report+='\n</details>\n\n## Not checked\n\n'
report+='No checkpoint or full store was copied. No real model/GPU execution, remote filesystem verification, host sandbox execution, full-population loader audit, complete component-lineage proof, benchmark evaluation, independent review or product end-to-end acceptance was performed. No official benchmark item or answer statistic chose a quantity, quota or threshold. All numerical outcomes above come from their cited receipts; no guessed population or resolution is used.\n'
(O/'BUILD_R1_REPORT.md').write_text(report)
(O/'BUILD9_REPORT.md').write_text('The preserved Build 9 report is [here](../work/build_n1/INHERITED_BUILD9_REPORT.md). The current R1 build report is [BUILD_R1_REPORT.md](BUILD_R1_REPORT.md).\n')
event=dict(type='RESULT',build='n1',lane='tree_rebuild',GO=False,review_requests=1,
 report='out/BUILD_R1_REPORT.md',seal=seal.get('tree_sha256'),package=delivery,
 request='One independent admission and legality review of the R1 training scope and changed inputs; no launch authorized.',
 publication='STAGED_LOCALLY_ONLY',blockers='work/build_n1/CARRIED_BLOCKERS.json')
(O/'RESULT_build_n1.json').write_text(json.dumps(event,indent=2)+'\n')
state='COMPLETE WITH NAMED BLOCKERS' if finished else 'FINAL QUALIFICATION IN PROGRESS'
(B/'STATUS.md').write_text('# Build n1 status\n\n'+state+'. GO=false.\n\n'
 'The current report is out/BUILD_R1_REPORT.md. Targeted native configuration, export/continuation, reader and sampler tests pass; exact outcomes are in proofs/targeted/results.json. Packet and frozen-suite outcomes are cited in the report.\n\n'
 'The loader audit remains blocked on complete scene-admitted populations, all-stream identities, frame-host preparation and final indices. Missing resolution, lineage evidence, staging closure, P boundary evidence and independent review remain named refusals in CARRIED_BLOCKERS.json.\n')
if finished:
 ledger=O/'DESIGN_RECORD_tree_rebuild_20261115.md';text=ledger.read_text();marker='\n## Build n1\n'
 if marker in text:text=text.split(marker)[0]
 ledger.write_text(text.rstrip()+marker+'\nThe R1 kit is staged with GO=false. It binds the parent export metadata, a receipt-selected VQA source and a capped configurable mix. Native CPU proofs cover export continuation, scale initialization, reader refusals and deterministic sampling. Full source admission and real frame-host evidence remain blocked.\n\n'
  'The authoritative report and complete blocker scope are [BUILD_R1_REPORT.md](BUILD_R1_REPORT.md). The source seal and package hashes are in `TREE_SEAL.json` and `../work/build_n1/DELIVERY.json`; suite counts and changed-statement coverage are in `../work/build_n1/SUITE_COMPARISON.json` and `../work/build_n1/N1_CHANGED_COVERAGE.json`. The single review request is staged in `RESULT_build_n1.json`. No job was submitted.\n')
print(json.dumps(dict(report='out/BUILD_R1_REPORT.md',state=state,bytes=len(report.encode()))))
