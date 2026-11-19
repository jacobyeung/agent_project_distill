import json, hashlib, sys, sqlite3, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w');W=BASE/'w21/work';TREE=W/'tree_r1'
sys.dont_write_bytecode=True;sys.path.insert(0,str(TREE))
from student_pilot.row_removals import Removals
d=json.loads((ROOT/'work/INVENTORY_STAGE.json').read_text());ledger=d['inputs']
def pin(p):
 p=Path(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 ledger[str(p)]={'sha256':h.hexdigest(),'bytes':p.stat().st_size}
 return {'path':str(p),'sha256':h.hexdigest()}
def ref(file,lines):
 p=TREE/file;return {**pin(p),'lines':lines}
def write(p,obj):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');return pin(p)
pin(Path(__file__));pin(ROOT/'work/INVENTORY_STAGE.json');pin(ROOT/'work/AUDIT_RUN.json')
rules=[]
def rule(field,requirement,file,lines):rules.append({'field':field,'requirement':requirement,'evidence':ref(file,lines)})
for args in [
('all pins','An exact {path,sha256} object; relocation may resolve a registered equivalent path, but the resolved path must be absolute, a file, and match SHA256. Extra pin keys refuse.','student_pilot/p3_provenance.py','43-51'),
('cfg.r1_training.row_sources','Pinned JSON with recovery, absolute_distance, units; coverage_distance and coverage_units must appear together. source_names returns these five for this config. Camera is not a source_names member.','student_pilot/r1_coverage.py','9-13'),
('coverage source hashes and wording_exclusion','Exact PINS values for both V2H sources; exact SPLIT=2463193d... with eight held-out templates, normalized with NFKC/casefold/whitespace. validate_binding authenticates sources and wording authority.','student_pilot/r1_coverage.py','5-7,18-48'),
('cfg.r1_training.row_slice_inputs','Optional staged source map; exact source-name set and SHA256 equality to row_sources. If absent, original sources are used.','student_pilot/r1_routing.py','162-170'),
('cfg.r1_training.routing_inputs','Mapping with a pinned manifest for every source_names name. Each is authenticated; no check rejects additional unused keys.','student_pilot/r1_routing.py','171-189'),
('cfg.r1_training.source_membership','Pinned schema r1-source-catalog-v1; exact family-name set; each source hash equals staged source hash; every admitted QID must be present in that family catalog.','student_pilot/r1_routing.py','172-178,189-191'),
('rows / family / stream / extent_receipt','Manifest rows pin equals the staged source object including path; family equals its map key; stream equals routing; extent_receipt equals cfg.extent_receipt including path.','student_pilot/r1_routing.py','180-188'),
('routing_base','Pin to c1-routing-stream-v1 receipt with scene_role train (missing defaults to train), heldout_overlap exactly 0, pinned division with train_scenes/heldout_scenes, pinned SQLite database with rows(i,row,target).','student_pilot/r1_routing.py','50-59,105-115'),
('request.routing_base / cfg.streams.routing','Entry request requires routing_base and routing_inputs and localizes them into config. Mode q reads the pinned config, requires s1_routing and routing_inputs, then native preparation regenerates the base and composes it. Bind both interfaces; do not substitute an export artifact.','launch_r1/entry.py','160-163'),
('mode-q config / regenerated base','The mode-q CPU producer checks config s1_routing/routing_inputs. s1_admission.prepare_phase builds a native base receipt and passes it into compose_native.','student_pilot/s1_admission.py','202-215'),
('schema / family','schema must be r2-family-manifest-v1 and family must be truthy. intake alone does not restrict family names; compose_native does.','student_pilot/r2_intake.py','32-35'),
('trace_contract / validator_sha256','Exact next-leg-r2-v1 and a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268.','student_pilot/r2_intake.py','36-37'),
('full-host environment','limit=None requires literal STUDENT_R2_FRAME_HOST=1, STUDENT_R2_LOCAL_NODE!=1 and a hostname not starting trinity. Otherwise limit must be an actual int in [1,2000]. compose_native always passes None. No host substitution was used here.','student_pilot/r2_intake.py','38-42'),
('scene_coverage','Must be non-None and an authenticated pin. Document exclusions equals manifest exclusions exactly; rows_sha256 equals manifest rows hash. Per-QID rows entries must have status known and nonempty names.','student_pilot/r2_intake.py','43-44,55-57,104'),
('scene_coverage.rows[QID]','Names normalize corpus aliases, use recognized corpora, include normalized dataset/scene and every row/provenance canonical. External evidence is required by the task; intake does not independently verify evidence fields or upstream identity provenance.','student_pilot/r2_exclusions.py','47-68'),
('exclusions','Exactly seven roles benchmark, dev_ids, eval_ids, frames_gate, eval_rooms, room_split, dev_manifest, with exact SEALED hashes. IDs are TSV column 2; remaining files are JSON. frames_gate is loaded but not applied by check.','student_pilot/r2_exclusions.py','5-44'),
('dev_scene_exclusions','Optional to intake, required in these drafts: merged-dev pin whose hash equals the sealed tree r2_dev_merged.json; NativeExclusions applies dev and benchmark. This is a1869ae2..., derived from dev-S1 969cdb56... plus withheld-80 634820b4....','student_pilot/r2_intake.py','46-51,107-108'),
('withheld_rooms','Optional pin defaults to sealed r2_withheld.json; supplied and actual bytes must equal 634820b4...; 80 unique rooms, seed 20261115, 40 scannet and 40 scannetpp. Row/coverage aliases are checked.','student_pilot/r2_withheld.py','8,19-45'),
('extent_receipt','Optional in generic intake but required by N exact equality; full-extent-receipt-v1. Required routing types/not_seen need QID, digest(content(normalized_row)), full box-status count matching independent_ordered_boxes, and repair digest equality. Frame joins are excluded from content.','student_pilot/extent_receipt.py','5-47'),
('upstream_receipts / prefiltered','upstream_receipts is iterated as pins; each receipt exclusions equals manifest exclusions and counts is a dict. Each count has exactly seen/admitted/refused/reasons, nonnegative actual integers, seen=admitted+refused, and reasons is a dict. Truthy prefiltered requires a nonempty authenticated list. Missing accounting stays MISSING; empty synthetic receipts are not used.','student_pilot/r2_exclusions.py','70-85'),
('frame_map / frame_plan / fps_authority','Optional generic inputs, necessary for these rows with no student_input.frames. With frame_plan, Frames loads gzip JSONL map and gzip JSON plan plus optional s1-fps-authority-v1. Without frame_plan, frame_map is a pinned per-QID JSON join.','student_pilot/r2_intake.py','59-66'),
('frame_map records / frame_plan','Map keys (d,s,i) must be unique, hashes lowercase 64 hex, path exactly /data2/k6tk/<first2>/<hash>.png. Plan v[scene] has dataset g and raw_n covering requested indices; only d3 permits max-index+1 lower bound when full count absent.','student_pilot/s1_routing.py','58-131'),
('fps_authority / source clocks','FPS must be finite positive, consistent with observed and pinned scene rates. Missing FPS may use source, scene authority, or genuinely uniform dataset rates. Source indices, hashes, total_num_frames and timestamps must agree.','student_pilot/s1_routing.py','91-150'),
('rows / row_bindings','Authenticated JSONL or gzip (detected from magic). Raw may wrap row; qid unique, must occur in row_bindings, whose value equals digest(raw), not line bytes or normalized row. digest uses sorted-key compact JSON, allow_nan=False.','student_pilot/r2_intake.py','20-29,70-89'),
('count','Required at report construction; descriptive population_count only. intake does not compare count to actual row cardinality. This lane computes the exact count independently.','student_pilot/r2_intake.py','120-123'),
('row lineage / normalize','Room-size rows need source_row_sha256 and frame_indices provenance. Normalize raw pools/events; missing RGB joins refuse, exact source ordinals must match.','student_pilot/r2_adapters.py','7-73'),
('routing_policy / artifact_heads','Optional both-path-20261116 invokes row_text_audit and routing_type_gate using artifact_heads (default []). Do not add a policy or head claim without source authority.','student_pilot/r2_intake.py','95-101'),
('row grammar / RGB metadata','Require qid,dataset,scene,student_input; 32 increasing unique indices starting 0; exact timestamps i/fps; valid total count and absolute frame pins. Program rows pass validate_program/shared grammar; direct rows pass validate_direct and type/unit gates; route_planning cannot enter routing.','student_pilot/r2_contract.py','124-192'),
('perception / select_types / mix_cells','perception adds pose/pointing checks; routing has no extra target_record constraint here. Optional select_types refuses other types. mix_cells[QID] is copied with no independent validation in intake.','student_pilot/r2_intake.py','80-81,103,118-119'),
('R0 / K1','Intake R0 reserve reads sealed r0_scenes f7c45817..., not the bdb5d402 room text directly. compose applies Filters then Rooms.admit for source rows; room_authority validates reserve bdb5d402 and teacher 4d4736cf and refuses K1. Extra required_exclusion_pins in draft is documentary, not a new intake gate.','student_pilot/r1_rooms.py','6-16,19-35,71-83'),
('admitted vs refused rows','Row KeyError/TypeError/ValueError becomes a refusal record; intake can return with refusals. compose_native consumes admitted rows, so a successful return alone does not prove all source rows admitted. Global dependency errors raise.','student_pilot/r2_intake.py','75-126'),
('composition downstream checks','Global duplicate QIDs refuse; base replacement cells skipped; filters enforce remove_files, training division, excluded QIDs and scenes; Rooms.admit and native reader run; reader failures count as refusals; source membership is recomputed; local database >200 MB refuses on Trinity.','student_pilot/r1_routing.py','9-47,77-103,105-159'),
('RGB staging / root alias','Q_E4 aliases STUDENT_FRAME_ROOT_MAP. resolve_frame uses longest absolute prefix, rejects traversal/symlink escapes and unresolved home/data roots, requires bytes; verify_frame hashes bytes. intake validate defaults require_frames=False and does not read RGB.','student_pilot/r2_frames.py','15-37,51-72'),
('frame admission audit','FrameAudit requires staged roots, exact frame pins, existence for every retained frame, no conflicting hashes, and deterministic seed-17 sample of 64 per source by default. An independent scene map is not a raster proof.','student_pilot/s1_admission.py','21-88'),
('frame-host alias patch','Current ALIASES has no frame-host key. sb_fhalias/tree_rebuild must supply naming-only reader changes and reseal, preserving all host/local/limit predicates; this lane writes no patch.','student_pilot/job_env.py','1-6')]:rule(*args)
d['contract']=rules
contract_pin=write('work/CONTRACT.json',{'schema':'fullinv-contract-v1','checks':rules,'inputs':dict(ledger)})
d['contract_artifact']=contract_pin
cfg=json.loads((W/'build21/inputs/config.json').read_text())
for p in cfg['remove_files']:pin(p['path'])
pin(TREE/'student_pilot/row_removals.py')
rem=Removals(cfg['remove_files']);removal={}
for name,s in d['slices'].items():
 if name=='camera_wording':continue
 with sqlite3.connect((ROOT/'work/audits_native'/name/'rows.sqlite').as_uri()+'?mode=ro&immutable=1',uri=True) as con:
  hits={qid for qid,hit in con.execute('select row_id,hits from rows') if 'K1' in json.loads(hit)}
 found=[];unremoved=[]
 with Path(s['source']['path']).open() as f:
  for line in f:
   r=json.loads(line)
   if r['qid'] in hits:
    matches=rem.match(r)
    (found if matches else unremoved).append(r['qid'])
 removal[name]={'K1_source_hits':len(hits),'matched_existing_remove_files':len(found),'unremoved_K1_qids':unremoved,'note':'Native row_keys only; this does not claim full filtering/admission.'}
 s['existing_removal_coverage']=removal[name]
 s['evidence']={'source_and_counts':[s['source'],pin(ROOT/'work/inventory.py')],'exclusion_result':[s['exclusions']['audit'],pin(ROOT/'work/AUDIT_RUN.json')],'scene_identity':[s['independent_coverage']['receipt'],d['independent_candidates'][0]['member_pin']],'frame_requests':[s['frames']['request_inventory']],'extent_binding':[s['extent']['pin'],pin(W/'build21/proofs/v2h/DERIVATIONS.json')],'dry_validation':[s['draft_envelope'],ref('student_pilot/r2_intake.py','32-126')]}
write('work/REMOVAL_COVERAGE.json',{'slices':removal,'command':'work/finalize.py: Removals.match on K1 QIDs from checker rows.sqlite','inputs':dict(ledger)})
listing=BASE/'ext/pwrap/LISTING_k_arm_runs.txt';listing_pin=pin(listing)
for name,size,lines in [('frame_map',14502816,'41'),('frame_plan',1518048,'42')]:
 d['frame_host']['metadata'][name]['recorded_remote_bytes']=size
 d['frame_host']['metadata'][name]['size_evidence']={**listing_pin,'lines':lines,'scope':'Recorded P kit listing, not current local or remote presence verification'}
kit=json.loads((BASE/'ext/pwrap/k/0.json').read_text())
size_entries={x['sha256']:x for x in kit['staged_inputs']['files']}
for db in d['frame_host']['required_store_databases']:
 entry=size_entries.get(db['database']['sha256'])
 if entry:db.update(recorded_remote_bytes=entry['bytes'],staging_source=entry['source'],size_evidence=pin(BASE/'ext/pwrap/k/0.json'))
 if db['local_status']=='EXISTS':
  db['local_pin_verified']=pin(db['database']['path']);assert db['local_pin_verified']['sha256']==db['database']['sha256']
d['frame_host']['kit_settings']=[
 {'setting':'cfg.streams.routing and request.routing_base','value':d['routing_base']['original_pin'],'evidence':ref('launch_r1/entry.py','160-163')},
 {'setting':'cfg.r1_training.routing_inputs and request.routing_inputs','value':'Five final, authenticated family-envelope pins; current drafts refuse','evidence':ref('student_pilot/r1_routing.py','171-191')},
 {'setting':'cfg.r1_training.row_slice_inputs','value':'Optional staged pins with unchanged source SHA256; envelope rows objects must equal these including path','evidence':ref('student_pilot/r1_routing.py','168-170,184-187')},
 {'setting':'Q_E4','value':'JSON absolute-prefix map from /data2/k6tk (and other required logical stores) to verified local frame-store roots','evidence':ref('student_pilot/r2_frames.py','15-37')},
 {'setting':'Q_E7','value':'Set to 1 only after sb_fhalias/tree_rebuild reader alias patch and frame-host stage validation; currently ignored. Keep local-node veto and non-Trinity hostname requirement. Q_E8 only if supplied by that separate approved alias build.','evidence':[ref('student_pilot/job_env.py','3-6'),ref('student_pilot/r2_intake.py','38-42')]},
 {'setting':'staging/identities','value':'Stage exact row, coverage, source catalog, extent, seven exclusions, five required exclusion authorities, merged dev, frame-map/plan/FPS, base division/database and all config-bound stores. Bind native preparation and source seal to the same receipts.','evidence':[ref('launch_r1/entry.py','143-165'),ref('student_pilot/s1_admission.py','182-215')]}
]
timing=json.loads((ROOT/'work/AUDIT_RUN.json').read_text());audit_seconds=sum(v['seconds'] for k,v in timing.items() if k!='inputs')
total_inventory=sum(s.get('seconds',0) for s in d['slices'].values())
d['timing']={'audit_seconds_measured':audit_seconds,'inventory_slice_seconds_measured':total_inventory,'timing_scope':'Elapsed seconds on one CPU process, <=8 library threads. Not a GPU or training benchmark.','command_audit':'nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B work/run_audits.py','command_inventory':d['command'],'evidence':[pin(ROOT/'work/AUDIT_RUN.json'),pin(ROOT/'work/INVENTORY_STAGE.json')]}
unremoved=sum(len(x['unremoved_K1_qids']) for x in removal.values())
d['production_ranked']=[
 {'rank':1,'owner':'main + tree_rebuild','produce':'Certify K1 exclusion in final retained composition using existing pinned removals: all 283 source hits already match removal keys. Produce authenticated accounting and retained-row census; no source repin is needed for those known hits.','remaining_K1_not_in_existing_remove_files':unremoved,'cpu_estimate':'1-5 seconds for row/list matching; 5-15 minutes engineering for authenticated accounting and retained census; no production launch included.','basis':[pin(ROOT/'work/REMOVAL_COVERAGE.json'),ref('student_pilot/r1_rooms.py','80-83')]},
 {'rank':2,'owner':'this lane (done)','produce':'23,886 digest(raw) bindings, five complete independent archived-map coverage files, six drafts, real intake dry runs, and five exclusion audits.','cpu_estimate':f'Measured {total_inventory:.2f} s slice inventory plus {audit_seconds:.2f} s checker processes.','basis':d['timing']['evidence']},
 {'rank':3,'owner':'main','produce':'Supply camera wording report and rows at /scratch/jjyeung/orch_n30/sb_rowA2/out/; supply pinned frame_map and frame_plan and current N frame-store inventory with byte sizes.','cpu_estimate':'Camera digest/audit approximately 1-10 seconds for a similar <25k-row source; 1-3 minutes to parse 14.5 MB compressed frame map once present. Availability wait MISSING.','basis':[listing_pin,pin(ROOT/'work/inventory.py')]},
 {'rank':4,'owner':'tree_rebuild + main','produce':'Produce genuine upstream exclusion-accounting receipts per prefiltered family; retain all source hashes, exact extent pin and all five exclusion rules. Bind final envelopes and N config/request. Confirm camera integration instead of appending an unsupported sixth family.','cpu_estimate':'1-5 minutes metadata validation after dependencies arrive; 15-30 minutes engineering estimate, not measured.','basis':[ref('student_pilot/r2_exclusions.py','70-85'),ref('student_pilot/r1_routing.py','162-194')]},
 {'rank':5,'owner':'tree_rebuild, separate sb_fhalias build','produce':'Frame-host environment alias patch, regressions and new source seal. No patch is written by sb_fullinv.','cpu_estimate':'1-5 minutes focused CPU checks; engineering/reseal estimate 15-30 minutes.','basis':[pin(W/'build21h/HOST_FLAG_BLOCKER.json'),ref('student_pilot/job_env.py','1-6')]},
 {'rank':6,'owner':'main on frame host','produce':'Join 56,640 scene/ordinal requests, stage actual required RGB and all native stores, verify retained-frame presence/hash sample, compose routing and native preparation. Exact PNG list/count/bytes remain MISSING until metadata is supplied.','cpu_estimate':'Join 1-3 minutes; presence audit roughly 1-5 minutes; hashing I/O B/(100-300 MB/s) plus file-open cost, B=MISSING. Full preparation/model CPU time MISSING without staged inputs. No transfers or raster scans run here.','basis':[ref('student_pilot/s1_routing.py','74-150'),ref('student_pilot/s1_admission.py','21-88'),d['routing_base']['local_pin']]}
]
d['claim_provenance']={'contract':'Each check has file, lines and sha256.','slices':'Each slice has evidence keyed by source/counts, exclusions, scene identity, frame requests, extent and dry-validation.','frame_host':'Metadata pins and recorded P manifests/receipts provide identity and reported sizes; absence is bounded to probed_paths, not a cluster-wide assertion.','production_ranked':'Each estimate is labeled and cites its measured or code basis; elapsed engineering estimates are not measurements.'}
d['inputs']=dict(ledger)
write('out/FULL_INVENTORY.json',d)
lines=[
'FULL native routing inventory: NOT READY. All five source pins verify; recovery/units contain K1 hits; camera input and full host dependencies remain incomplete.',
'All paths and full SHA256 values, code checks, scene lists, frame requests, drafts and timings are in `FULL_INVENTORY.json` and `../work/`. `T` below is `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w21/work/tree_r1`.',
'Five authorities: R0 `bdb5d402`, dev-S1 `969cdb56`, BENCH v2 `3119aa4a`, withheld-80 `634820b4`, K1 `4d4736cf`; every draft records their full pins. Checker PASS means complete resolution, not zero hits.',
'Counts come from `work/inventory.py` (JSONL count, native digest(raw), distinct scene/ordinal set) and `work/run_audits.py` (real sb_auditfix2 checker). Run both with `nice -n 10`, OMP/MKL/OPENBLAS_NUM_THREADS=8, CUDA_VISIBLE_DEVICES empty, and `/scratch/jjyeung/envs/p1cpu/bin/python -B`.',
''
]
for name in ('recovery','absolute_distance','units','coverage_distance','coverage_units'):
 s=d['slices'][name];hits=s['exclusions']['hits'];e=s['extent'];b=s['existing_removal_coverage']
 lines += [f'| {name}: source and binding | Independent coverage / exclusions | Frames / envelope |',
 '|---|---|---|',
 f"| `{s['source']['path']}`; SHA `{s['source']['sha256']}`; {s['rows']:,} rows and digest bindings; {s['source_bytes']:,} bytes; CPU inventory {s['seconds']:.2f}s + checker {timing[name]['seconds']:.2f}s | {s['scene_count']:,} scenes; archived original map independently covers all rows; zero R0/dev/BENCH/withheld; K1={hits['K1']}; existing removal matches {b['matched_existing_remove_files']} | {s['frames']['references']:,} frame references / {s['frames']['unique_scene_ordinals']:,} unique scene/ordinals; physical count, PNG paths, bytes and N stage=MISSING. Extent `c072905b`: {e['qid_entries']:,} entries; envelope `work/envelopes/{name}.json`; upstream accounting and map/plan=MISSING. |",
 '' ]
lines += [
'| Camera wording | Independent coverage / exclusions | Frames / envelope |','|---|---|---|',
'| `/scratch/jjyeung/orch_n30/sb_rowA2` is absent; row path, pin and count=MISSING | Scene evidence, checker and extent row binding=MISSING | Frames/bytes/stage=MISSING; `work/envelopes/camera_wording.json`; integration family requires tree owner because source_names has only five entries. |','',
'| Envelope contract | Exact checks (paths relative to T) |','|---|---|',
'| Pins, family, count | Exact `{path,sha256}`, absolute/hash-verified (`p3_provenance.py:43-51`); schema/family (`r2_intake.py:34-37`); count is reported, not compared to cardinality (`:120-123`). |',
'| Composition | Five names and fixed V2H/wording pins (`r1_coverage.py:5-48`); staging hashes, catalog schema/hash/QID membership; rows/family/stream/extent exact equality (`r1_routing.py:162-191`). |',
'| Native contract | `trace_contract=next-leg-r2-v1`; validator `a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268`; per-QID digest of raw JSON, no duplicate QIDs (`r2_intake.py:36-37,76-88`). |',
'| Coverage | Pinned coverage exclusions equal envelope exclusions, rows_sha256 matches rows; QID status=known, names include native and canonical identities (`r2_intake.py:55-57`; `r2_exclusions.py:47-68`). All five coverage files are produced from verified archived map `488480ab`, not row canonical claims. |',
'| Exclusions | Exactly seven SEALED roles (`r2_exclusions.py:5-44`); merged dev `a1869ae2` and withheld checks (`r2_intake.py:45-54,93-108`); R0/K1 room authority is additionally enforced in composition (`r1_rooms.py:19-35,71-83`). Documentary five-pin fields do not add intake checks. |',
'| Upstream | Receipt pins must bind identical exclusions and valid seen=admitted+refused counts; prefiltered needs nonempty receipts (`r2_exclusions.py:70-85`; `r2_intake.py:67-68`). No authenticated family accounting identified. |',
'| Extent | Exact config pin `c072905be4405a92d7bb906112209f2d27a8c9b58d291b64373c5551c3e96495`; normalized content/repair digest, full box counts (`extent_receipt.py:5-47`). All 6,000 V2H rows pass exact rewording/inherited-entry checks; no synthetic frames or new geometry proof supplied. |',
'| RGB metadata | gzip map (d,s,i)→content-addressed PNG, plan raw_n and dataset, FPS authority; 32 ordered anchors and clock/hash agreement (`s1_routing.py:58-150`; `r2_contract.py:124-140`). Map/plan missing; FPS `36ae882f` exists (47,800 bytes). |',
'| Grammar / optional fields | Normalize, event/direct grammar, units and type checks; optional both-path policy/heads; mix_cells copied; row failures become refusals (`r2_adapters.py:7-73`; `r2_contract.py:143-207`; `r2_intake.py:95-126`). Full field/check inventory is `work/CONTRACT.json`. |',
'| Full host / first failures | Every draft with limit=None fails `r2_intake.py:42`: Local slices must contain at most 2000 rows per family. With 2000, five fail upstream MISSING at `r2_intake.py:58`→`p3_provenance.py:46`; camera fails scene_coverage MISSING at `:55`→`:46`. No hostname or function substitution. |',
'| routing_base | P step-400 receipt `ca0616db…` is c1-routing-stream-v1/train/zero overlap, database `4e8e6c04…`, division `f41d15aa…`; `ext/m400real/r.json` binds its config. Set request.routing_base AND cfg.streams.routing; mode q uses config and preparation regenerates the base (`launch_r1/entry.py:160-163`; `s1_admission.py:202-215`). |','',
f"The five slices share {d['frame_host']['unique_scene_ordinals_all_five']:,} distinct scene/ordinal requests. Their exact PNG paths/bytes require the missing map `17aa3e9e` and plan `7cc01f36` at the config's `/scratch/fsw/.../8865619b/k/` paths. P's listing records 14,502,816 and 1,518,048 bytes; current N staging is unproved.",
f"The frame host must hold those PNGs under mapped `/data2/k6tk`, map/plan/FPS, all source rows/envelopes/coverage/exclusions/extent/catalog, routing/base division and native stores. P's recorded k6tk bundles total {d['frame_host']['recorded_P_archive_bytes']:,} bytes/{d['frame_host']['recorded_P_archive_members']:,} members; these are not N subset totals. JSON lists all archive paths and P frame-audit roots.",
'N VQA store `210b2534` exists locally: 1,718,255,616 bytes. Pointing `c09bb5ca` is recorded as 218,099,712 bytes; routing base `4e8e6c04`, pose `b32359ce`/`0b95850a` sizes remain MISSING. JSON lists exact store paths, pins, provenance and staging status.',
'The kit needs exact staged family/source/catalog/extent pins in config and request, Q_E4 absolute frame-root mappings, and verified frame admission. Q_E7=1 works only after sb_fhalias/tree_rebuild adds the alias and reseals; this lane writes no alias patch. Preserve the non-Trinity/local-node/limit vetoes.',
'',
'| Rank / owner | Required production and CPU estimate |','|---|---|',
 f'| 1 main + tree_rebuild | Certify final retained K1 exclusion: existing removals cover all 283 source hits ({unremoved} unmatched). Produce accounting/census; no new source pin needed for these hits. Matching: 1–5 s; integration estimate: 5–15 min. |',
f'| 2 this lane — done | Digests, independent coverage, six drafts and dry checks: {total_inventory:.2f} s; five exclusion audits: {audit_seconds:.2f} s measured. |',
'| 3 main | Supply camera report/rows and pinned map/plan plus current frame inventory. Camera audit estimate 1–10 s; map parse/join 1–3 min once present; availability wait MISSING. |',
'| 4 tree_rebuild + main | Authenticate upstream receipts, finish envelopes and config/request bindings, decide camera integration. Metadata checks 1–5 min; engineering estimate 15–30 min. |',
'| 5 tree_rebuild / sb_fhalias | Separate naming-only alias patch and new seal. Focused CPU checks 1–5 min; engineering estimate 15–30 min. |',
'| 6 main on frame host | Stage exact RGB/stores, compose, prepare and audit every retained frame plus fixed hash sample. Presence estimate 1–5 min; hash time B/(100–300 MB/s), B=MISSING; full preparation CPU time MISSING. |',
'',
'Estimates assume ≤8 CPU threads and available local inputs; no transfers, RGB reads, GPU, network, launcher, tmux, Git or foreign writes occurred. No revision-history wording is retained.'
]
assert len(lines)<=70,len(lines)
(ROOT/'out/FULL_INVENTORY.md').write_text('\n'.join(lines)+'\n')
(ROOT/'STATUS.md').write_text('The inventory report, machine-readable evidence ledger, independent scene coverage, exact row bindings and six envelope drafts are complete. The report records K1 source hits, existing-removal coverage, actual intake failures, missing camera/map/plan/staging evidence, exact host contracts and owner-ranked CPU estimates. Packaging and consistency verification remain.\n')
print('REPORT',len(lines),'lines; removal coverage',json.dumps(removal),'timing',audit_seconds,total_inventory)
