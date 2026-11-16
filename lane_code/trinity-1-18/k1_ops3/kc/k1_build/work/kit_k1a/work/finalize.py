"""Write the current evidence, run card, and precise outstanding input questions."""
import collections,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
L=Path(__file__).resolve().parents[1];O=L/'out';R=gate.ROOT
inv=json.loads((O/'CAPTURES.json').read_text());plan=json.loads((O/'K1_MANIFEST.template.json').read_text())
facts=json.loads((O/'K1_PLAN_RESULT.json').read_text());p2=json.loads((O/'P2_RESULT.json').read_text())
sys.path.insert(0,str(R/'o3_cache/work/kit'))
import bindings as B
names={(c['canonical'],B.kitlib.normalize_phrase(n)) for c in plan['captures'] for r in c['rows'] for n in r['operands']}
prompts=sum(1+len(B.variantlib.aliases(n)) for _,n in names)
timing=dict(captures=len(plan['captures']),unique_capture_operands=len(names),prompt_calls=prompts,
 sam_hours_low=prompts*(1499/785)*1.2/3600,sam_hours_high=prompts*(1004/486)*1.6/3600,
 geometry_hours=300*24.6/3600,source_rates=str(R/'devs1_masks/out/RUNCARD.md'),
 source_geometry=str(R/'o3_cache/out/CACHE_KIT_REPORT.md'),measured=False,
 assumptions='Per-prompt baseline times multiplied by dense factor 1.2–1.6; aliases counted explicitly; geometry 24.6 seconds/capture; excludes CPU rendering, transfers and model loads')
(O/'GPU_ESTIMATE.json').write_text(json.dumps(timing,indent=2)+'\n')
deps={str(p):gate.sha(p) for p in sorted((R/'o3_cache/work/kit').glob('*.py'))}
deps.update({str(p):gate.sha(p) for p in sorted((R/'o3_cache/work/kit/vendor_sam').rglob('*.py'))})
deps.update(B.source_identity())
for rel in ['o3_cache/out/CUE_STUDY.md','o3_cache/out/CUE_METRICS.json','sam3_tower/out/BATCH_MEASUREMENTS_FINAL.json','grd_selector/work/setsel/build.py','grd_selector/work/setsel/fit.py','grd_selector/work/setsel/fit_pairs.py','rs_tree/work/tree_r1/student_pilot/r1_contract.py']:
 deps[str(R/rel)]=gate.sha(R/rel)
(O/'DEPENDENCIES.json').write_text(json.dumps(deps,indent=2)+'\n')
local_gt=sum(c['gt']['bytes'] for c in inv['pilot'])
io=dict(exact_frame_staging_bytes=None,exact_total_staging_bytes=None,selected_gt_regular_file_bytes=local_gt,
 source_map=str(O/'FRAME_SOURCES.jsonl'),selected_plan=str(O/'K1_MANIFEST.template.json'),
 unresolved_dense_captures=plan['unresolved_dense_sources'],approval_required=True,transfer_performed=False,
 original_frame_store='/data2/k6tk',recorded_replica='/project/community/jjyeung/cp4tk_fr/k6tk',
 additional_dense_lead='trinity-3-30:/scratch/jjyeung/frames64 (recorded in o3_cache/out/CACHE_KIT_REPORT.md; current availability unverified)',
 reason='The source MAP has no per-PNG sizes; selected sparse-only captures have no complete dense RGB source in available metadata')
(O/'STAGING_REQUIREMENTS.json').write_text(json.dumps(io,indent=2)+'\n')
(O/'HEAVY_IO_QUESTION.md').write_text(f'''The staging request is not yet numerically complete. Do not stage from this packet.

The selected pilot has {facts['captures']} captures and {facts['mapped_planned_frames']} mapped planned RGB files; {facts['unresolved_dense_captures']} captures lack the required dense sequence (out/K1_PLAN_RESULT.json). Exact RGB bytes and total staging bytes are **unknown**, not zero. The map contains paths and SHA256 values but no PNG sizes (p1c_build/k6/MAP.jsonl.gz, pinned by out/CAPTURES.json).

The selected local GT files total {local_gt} regular-file bytes (out/STAGING_REQUIREMENTS.json). This is a GT total, not an RGB staging estimate. GT file contents and full hashes await production preflight; the inventory checked ZIP headers and the planner read only IDs, labels, and frame indices.

Every known RGB source path and hash appears in out/FRAME_SOURCES.jsonl. out/K1_MANIFEST.template.json restricts that list to the pilot's planned samples. The original mapped store is /data2/k6tk. The recorded Orchard replica is /project/community/jjyeung/cp4tk_fr/k6tk. o3_cache/out/CACHE_KIT_REPORT.md names trinity-3-30:/scratch/jjyeung/frames64 as a possible dense source; its current availability is unverified. No remote host or shared RGB path was probed.

Required operator answer: identify a current dense RGB source for the captures in out/STAGING_REQUIREMENTS.json, return a manifest with exact member bytes and hashes, and approve one archive staging operation after its total is known. No transfer command is authorized by this document. Preserve the fixed pilot. Never reconstruct geometry from only its sparse anchors.

Use one archive transfer at a time. Reads/downloads through shared storage or the head node stay at 8 MB/s; shared-storage writes stay at 4 MB/s. The user's aggregate cap is 18 MB/s, with writes counted twice. Plan any transfer above about 30 GB through those paths with an admin. Compute-to-compute transport uses the approved InfiniBand archive pipe. Extract only on /scratch and preserve the free-disk reserve. This lane holds no staged media.
''')
lo=timing['geometry_hours']+timing['sam_hours_low'];hi=timing['geometry_hours']+timing['sam_hours_high']
(O/'RUNCARD_K1.md').write_text(f'''K1 is a prepared, fail-closed run kit. **Do not launch the supplied template.** It lacks dense RGB for {facts['unresolved_dense_captures']} selected captures, exact staging bytes, verified local model settings, and reviewed fallback traces (out/K1_PLAN_RESULT.json; out/GPU_SETTINGS.template.json). No GPU ran.

The required p1cpu interpreter has PyTorch 2.11.0+cpu and no compiled CUDA support (out/GPU_ENVIRONMENT_METADATA.json). Its commands below are a conditional run sequence, not an executable GPU launch on this environment. The user's standing instruction keeps non-fit work on p1cpu. A GPU-capable interpreter therefore needs explicit authorization and a compatibility proof before the GPU launcher can be made operational. This lane installs nothing and silently substitutes no interpreter.

The fixed pilot contains 300 captures: 51 ScanNet, 87 ScanNet++, and 162 ARKitScenes. Physical-room splitting with seed 17 yields 242 training and 58 held-out captures (out/INVENTORY_RESULT.json; exact membership in out/CAPTURES.json). K1's held-out rooms remain training-corpus rooms; the separate `k1_split` field controls fitting.

The pipeline first caches unselected proposals and checkpoint-scaled geometry. It then builds label-free candidate features, fits on K1 training rooms, and renders with that refit. The current selector may run only in explicit CPU fixture proofs. It never renders K1 training responses.

Frozen settings: dense_aliases, joint floor 0.05, per-prompt cap 30, merged cap 100, linker floor 0.3, mask threshold 0.5, SAM resolution 1008, BF16, batch one. G3T reconstructs a complete declared dense sequence before selecting the 32 anchors. geometry.convert uses the step-544 private heads for one scale application and gravity. The native candidate policy retains its interior depth cut and fit_gbox_policy_voteb5_best1_v1 box policy. Sources: legs1_routed/out/ROUTED_READ_SPEC_NOMDG.md; o3_cache/work/kit/pipeline.py and boundaries.py.

Estimated GPU work is {lo:.2f}–{hi:.2f} hours, including {timing['geometry_hours']:.2f} hours for geometry and {timing['sam_hours_low']:.2f}–{timing['sam_hours_high']:.2f} hours for {prompts} prompt calls. This extrapolates the named devs1_masks rates and the geometry estimate; it is not a measured K1 timing. CPU selection/rendering, model loads, and offloading are additional (out/GPU_ESTIMATE.json). Start with an operator-reviewed capture smoke before extrapolating the full run.

Before execution, the operator must:

1. Close out/HEAVY_IO_QUESTION.md and stage complete dense RGB on the assigned node. Complete and hash the production manifest; do not substitute sparse anchors. Mark `frame_staging_authorized` and `production_ready` true only after closure. Empty unresolved-source lists must reflect real input closure.
2. Complete every required model setting in out/GPU_SETTINGS.template.json with verified local paths and hashes. The known artifact/config/G3T/SAM hashes are already bound; model payload locations remain pending. Bind each model row's native fps, timestamps, total frame count, and scene identity from source metadata. Use the accepted step-544 artifact and matching config/data receipt, frozen E0 G3T weights/config, and frozen SAM checkpoint/source receipt. Nothing installs or downloads.
3. Supply reviewed visual fallback traces through each row's `fallback` field. Missing evidence produces an excluded row. GT enters only classification and fitting labels; no GT value is copied into a runtime response.
4. Check the cluster allocation board, choose one compute node and card, and use the operator's persistent session. Bind a node-local copy of the existing vnice.sh. This lane selects no card and launches no job.
5. Run work/verify_sources.py. A changed dependency requires review and revalidation, not a silent pin refresh.

Commands, from this lane's directory on the staged node:

```bash
bash work/run_k1.sh NODE CARD /scratch/jjyeung/k1/manifest.json /scratch/jjyeung/k1/cache /scratch/jjyeung/tools/vnice.sh
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/k1_pipeline.py tables --manifest /scratch/jjyeung/k1/manifest.json --cache /scratch/jjyeung/k1/cache --out /scratch/jjyeung/k1/tables
/scratch/jjyeung/envs/planner_local_v1/bin/python -I -B work/refit/train.py --candidates /scratch/jjyeung/k1/tables/candidates.jsonl --pairs /scratch/jjyeung/k1/tables/pairs.jsonl --inventory out/CAPTURES.json --out /scratch/jjyeung/k1/refit
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/k1_pipeline.py render --manifest /scratch/jjyeung/k1/manifest.json --cache /scratch/jjyeung/k1/cache --fit /scratch/jjyeung/k1/refit --out /scratch/jjyeung/k1/rendered
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/k1_report.py --rows /scratch/jjyeung/k1/rendered/K1_ANALYSIS_INPUT.jsonl --inventory out/CAPTURES.json --manifest /scratch/jjyeung/k1/manifest.json --fit /scratch/jjyeung/k1/refit/FIT_RECEIPT.json --out /scratch/jjyeung/k1/K1_RESULT.json
```

The refit writes MODELS.json (`coef` for frozen pricing), NATIVE_POLICY.json (`coefficient` and `pair` for the native policy), and the original pickle bundles. Every fit receipt records Python, NumPy and scikit-learn versions, input/source hashes, and room splits. The fixed policy thresholds are inherited constants; no K1 label tunes them. The constant-answer baseline uses training rooms only. K1 reports AUC/AP/top-one metrics for both models on identical held-out candidates.

The cache writes append-only PROGRESS.jsonl and per-capture receipts. Resume checks source, manifest, geometry, and proposal hashes. A partial capture or HALTED run refuses resume. The watchdog supervises only its own child; it halts after 900 seconds without a capture commit or 21,600 wall seconds. It never retries. A clean time/STOP boundary returns 4. Write RESUME into the existing STOP file only after the operator authorizes continuation. An unexpected cluster kill must be reported and reviewed before any rerun.

The output cap is 1.5 GB and the run requires a 100 GiB free-space reserve in addition to that cap. Use at most eight CPU threads; this card defaults to one. The build lane remains below its separate 2 GB cap. Large raw proposal JSON may hit the bounded 20 MB reader; that failure requires a streaming format change before continuing.

Live parity: work/parity_live.py --print-command prints the command for a manifest containing exactly ten eligible scenes. The cache stage retains parity_raw.jsonl before merging. Its entries bind frame bytes, verbatim raw prompt, cached per-prompt response and SAM settings. The harness runs the real encode/detect path at the dense floor/cap and the tower's noise-aware rule. Merged alias records cannot substitute because merging reindexes proposal IDs. CPU KIT exercises raw-record collection; production collection and real GPU parity remain unverified.

Build the fixed ten-scene manifest from completed cache outputs:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/parity_live.py --prepare --manifest /scratch/jjyeung/k1/manifest.json --cache /scratch/jjyeung/k1/cache --out /scratch/jjyeung/k1/PARITY_10.json
```

Each rank must run the actual row admission before its first batch:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/first_batch.py --rows RANK_FIRST_ROWS.jsonl --contract SEALED_MEMBERSHIP_CONTRACT.json --rank RANK --out RANK_FIRST_BATCH_RESULT.json
```

rs_tree must seal production membership itself. out/FIRST_BATCH_32.jsonl and out/FIRST_BATCH_CONTRACT.json are synthetic CPU fixtures and confer no training admission. No patch to a seal tree is required or supplied.
''')
proofs=[]
for name in ['P1','P2','P3','P4','P5','P6','P7','KIT','HANDOFF']:
 p=O/(name+'_RESULT.json');r=json.loads(p.read_text());proofs.append((name,r))
lines=['CPU proof status. All paths below are relative to this lane. Real GPU parity, learned K1 accuracy, media staging, and production training admission are not measured.','', '| Proof | Status | Evidence |','|---|---|---|']
for name,r in proofs:lines.append(f"| {name} | {r['status']} | out/{name}_RESULT.json; out/{'P2_LINE_HITS' if name=='P2' else name+'_COVERAGE'}.json |")
lines+=['',f"P2 uses {p2['interpreter']}, Python {p2['python']}, NumPy {p2['numpy']}, and scikit-learn {p2['sklearn']}. The maximum absolute coefficient/scaler/intercept difference is {p2['largest_difference']} (out/P2_RESULT.json). No fixture fit model is deployed.",
'','P3 executes the shared frozen pricing comparator on real read-only dev-S1 proposals and geometry. It compares unrounded prices and errors exactly; it does not assert that the native printed response equals an unrounded old price. The native renderer is exercised separately by P4 and KIT. The dev-S1 fixture never enters a training fit.',
'','P4 executes the reused o3_cache producer through real geometry conversion, proposal processing, selection and runtime calls, with stand-ins only at neural boundaries. Mutation checks reject GT response injection and refusal-ending fallback. Response spans include delimiters and carry zero loss. HANDOFF excludes failures without reviewed visual fallback evidence.',
'','P5 runs the actual refit/export path on labelled synthetic feature rows from the fixed eligible room split. It rejects extra label-derived feature columns and benchmark captures. The result is marked fixture_only. Learned metrics on real K1 candidates remain unmeasured.',
'','P6 runs the actual SAM tower encode/detect path with a CPU neural stub and recorded raw-prompt cache entry. It rejects a shifted frame, swapped phrase, and 0.05 score drift. It makes no real GPU parity claim.',
'','P7 runs rs_tree Admission.check with real synthetic PNGs and sealed fixture membership on trust/fallback rows. out/FIRST_BATCH_CLI_RESULT.json verifies the handoff command. Production membership, provenance review, and tokenizer-level distributed first batches still belong to rs_tree.',
'','Coverage files record executed lines, AST statement lines and missing statements. P2 records exact line hits in the unchanged source files. GPU-only and unexecuted branches remain visible; coverage is not represented as complete.',
'','Logs: out/P1.log, out/P2.log, out/P3.log, out/P4_P7.log, out/P5.log, out/P6.log, out/KIT.log, out/HANDOFF.log.']
(O/'PROOFS.md').write_text('\n'.join(lines)+'\n')
design=f'''Question: can the repair seal ground eligible training rows with the frozen backend while excluding every protected room?

Answer: the CPU kit passes its proofs and enforces the gate/refit/render order. A real K1 run is not admitted because its dense RGB and staging inventory are incomplete. The run card is conditional on those inputs. No eligible learned refit or production response cache is claimed.

Evidence: out/CAPTURES.json lists every capture behind the requested pool row types. out/GATE_RECEIPT.json binds the exclusion authorities and selected membership. out/P2_RESULT.json reproduces both deployed models exactly. out/PROOFS.md records every proof and its scope. out/K1_PLAN_RESULT.json records {facts['unresolved_dense_captures']} missing dense-source captures and {facts['rows']} planned rows. Exact RGB bytes are unknown (out/STAGING_REQUIREMENTS.json).

Design choices and rejected options:

- Use the strict physical-room gate with known aliases. Reject direct capture-only exclusion because rescans and ARKit venue siblings leak rooms.
- Keep the unchanged fit estimators and fit only K1 training rooms. Reject rendering training responses with the deployed model because its fit rooms include protected benchmarks. The authorized sklearn interpreter remains read-only; no installation occurs.
- Cache neural outputs before fitting. Reject a combined cache-and-render launch with current selector weights. Candidate features run without labels; GT attaches only after feature production. The build adapter calls original build.py set_features/iou and unchanged native feature functions; the fit and pair estimators are imported unchanged.
- Preserve the requested pilot and dataset proportions. Reject silently replacing captures missing dense RGB, because that would change the pilot rather than close its inputs.
- Reconstruct geometry before anchor selection. Reject fitting on the mapped sparse anchors. Input closure requires actual dense frames with hashes, not fabricated paths or byte totals.
- Use native event rendering and runtime statuses. Reject GT-valued tool responses, unverified fallback traces, final refusals, and unmasked response spans. Missing reviewed fallback evidence excludes a row.
- Reuse o3_cache pipeline.proposals, classification, mask agreement, event rendering, neural boundaries and CPU fixture; reuse its cue-study directions and explicit distinction between printed cues and candidate proxies. Reject treating dev-84 proxy AUROCs as held-out K1 printed-cue evidence. Exact dependencies are pinned in out/DEPENDENCIES.json.
- Retain fixed policy constants and preregister K1 kill rules before GPU output. Reject label-dependent quotas or threshold sweeps. Fit the constant-answer baseline only on training rooms.

Options considered for missing staging bytes: use an average PNG estimate, inspect every shared-storage PNG, or request a source inventory. An average cannot supply exact bytes, and shared-storage inspection needs approval. The kit requests a source inventory and leaves the exact field null.

Risks and how to notice them:

- Sparse or missing RGB fails manifest preflight. Source staging must close every entry in out/STAGING_REQUIREMENTS.json.
- GT headers do not prove raster contents or frame alignment. Production preflight checks hashes and table/renderer readers check anchor order and raster shape.
- Native and frozen pricing paths have different output precision and geometry contracts. P3 checks frozen prices exactly; P4/KIT check native response bytes. Real GPU geometry and live/cache parity must run before a product claim.
- The required p1cpu environment is CPU-only (out/GPU_ENVIRONMENT_METADATA.json). A GPU-capable interpreter needs explicit authorization because the user allows only the named selector exception. A staged one-capture smoke must then settle compatibility, memory and timing. No alternative interpreter is silently used.
- Dependencies live in other read-only lanes and can change. work/verify_sources.py refuses changed source pins.
- Large raw JSON, complex masks, or long capture times may exceed bounded readers, disk limits or the watchdog. Preserve the failed attempt and review it; do not retry a killed job.
- Fixture model receipts are not eligible learned models. The production renderer refuses fixture_only fits.

Tests that settle the remaining questions: approved dense-source audit; real one-capture GPU smoke; raw-prompt live/cache parity on ten eligible scenes; unchanged refit on real K1 candidates; held-out K1 kill-rule report; and each rank's first batch through sealed production membership.

Status: CPU proofs and conditional run kit delivered. Real K1 fit/metrics/cache, complete dense input closure, exact RGB staging bytes, and production row admission remain pending. All lane writes stay local; no GPU, staging, network connection, installation, Git operation, or subagent ran.

Reader-first writing audit: no revision-history sentences retained. Evidence limitations and pending inputs remain because consumers need them to assess readiness.
'''
(O/'DESIGN_RECORD.md').write_text(design);(O/'DESIGN_RECORD_b6_build_20261115.md').write_text(design)
status='; '.join(name+' '+r['status'] for name,r in proofs)
(L/'STATUS.md').write_text(f'''B6-A CPU proof status: {status} (out/PROOFS.md). P2 reproduces both deployed models exactly under the authorized planner_local_v1 interpreter; every fit receipt records its versions. Original fit code is unchanged.

The gate selects 300 eligible captures with zero refusals; the physical-room split has 242 train and 58 held-out captures (out/INVENTORY_RESULT.json). The synthetic 32-row handoff passes rs_tree admission (out/P7_RESULT.json; out/FIRST_BATCH_CLI_RESULT.json).

The conditional run kit and preregistered kill rules are delivered (out/RUNCARD_K1.md; out/K1_RULES.json). GPU readiness is BLOCKED: {facts['unresolved_dense_captures']} captures lack mapped dense RGB, exact RGB staging bytes are unknown, model/video metadata needs verified local pins, and real fallback traces need review. The required p1cpu interpreter is CPU-only; a GPU interpreter needs explicit authorization (out/GPU_ENVIRONMENT_METADATA.json). No real K1 fit/cache or learned metrics are claimed. out/HEAVY_IO_QUESTION.md states the source-inventory/approval need.

No GPU, staging, SSH, Git, subagent, installation, shared-storage search, or shared-storage write occurred. Consumers read this lane's handoff artifacts; other trees remain untouched.
''')
sizes=[(str(p.relative_to(L)),p.stat().st_size) for p in L.rglob('*') if p.is_file()]
size=sum(n for _,n in sizes);assert size<2_000_000_000,size
(O/'STORAGE_RECEIPT.json').write_text(json.dumps(dict(regular_file_bytes=size,cap_bytes=2_000_000_000,largest_files=sorted(sizes,key=lambda x:-x[1])[:12]),indent=2)+'\n')
print(json.dumps(dict(proofs=status,storage_bytes=size,gpu_hours=[lo,hi],dense_sources_pending=facts['unresolved_dense_captures']),indent=2))
