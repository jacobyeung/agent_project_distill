from common import *
seen=start('finalize.py')
build=load(ROOT/'out/BUILD.json');classification=load(ROOT/'out/CLASSIFICATION.json');edits=load(ROOT/'out/EDITS.json');rebind=load(ROOT/'out/REBIND.json');intake=load(ROOT/'out/INTAKE.json');verify=load(ROOT/'out/VERIFY.json');source=load(ROOT/'out/SOURCE_FORMS.json');grammar=load(ROOT/'out/GRAMMAR_CHECKS.json');audit=load(ROOT/'out/room_audit/audit.json');sample=load(ROOT/'out/READ40_INDEX.json')
seal_path=BASE/'tree_rebuild10_w/w24/out/TREE_SEAL.json';seal=load(seal_path)
assert seal['tree_sha256']=='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7'
assert intake['aggregate']==dict(seen=5979,admitted=5143,refused=836)
assert intake['reasons']=={'excluded:eval_rooms':836}
assert verify['gt_recomputed']==5979 and not verify['gt_failures'] and not verify['wording_hits'] and not verify['instantiated_heldout_template_hits']
assert audit['complete'] and audit['rows']==5979 and audit['unresolved_rows']==0 and all(v==0 for v in audit['hits'].values())
assert sample['count']==40
# Revalidate all recorded local input hashes, including every opened tree dependency.
inputs={};conflicts=[]
for report in [build,classification,edits,rebind,intake,verify,source,grammar,audit,sample]:
 for p,v in report['inputs'].items():
  if p in inputs and inputs[p]['sha256']!=v['sha256']:conflicts.append(p)
  inputs[p]=v
assert not conflicts,conflicts
for p,v in inputs.items():
 assert str(Path(p).resolve()).startswith('/scratch/'),p
 pin(p,v['sha256'])
assert pin(ROOT/'work/route.py')['sha256']==pin(ROUTE/'work/route.py')['sha256']
assert pin(ROOT/'work/intake_reference.py')['sha256']==pin(ROUTE/'work/intake.py')['sha256']
# Verify exact independent coverage entries, QID partition, and exclusion-only refusal population.
newcov=load(rebind['coverage']['path']);oldcov=load(ROUTE/'out/coverage/camera_wording_final.json')
assert newcov['rows']==oldcov['rows'] and len(newcov['rows'])==5979
assert newcov['rows_sha256']==build['rows']['sha256']
assert set(r['qid'] for r in rebind['excluded'])==set(r['qid'] for r in intake['refusals'])
allq=set()
for shard in intake['shards']:
 with gzip.open(shard['rows']['path'],'rt') as f:qs={json.loads(line)['qid'] for line in f}
 assert not allq&qs;allq|=qs
assert allq==set(build['row_bindings'])
# Cross-check each selected before/after pair against the authenticated row populations.
samples={r['qid']:r for r in sample['rows']}
for r in rows(SOURCE):
 if r['qid'] in samples:assert r['target']==samples[r['qid']]['before']
for r in rows(build['rows']['path']):
 if r['qid'] in samples:assert r['target']==samples[r['qid']]['after']
# Preserve all cell deficits in a separate plain table and the consolidated JSON.
cell_lines=['| Wording | Displacement | Rotation | Direction |','|---|---:|---:|---:|']
for i in range(40):
 t=f't{i:02d}'
 vals=[verify['cells'][typ+'|'+t]['admitted'] for typ in ['camera_displacement','camera_rotation','camera_movement_direction']]
 cell_lines.append('| '+t+' | '+' | '.join(map(str,vals))+' |')
(ROOT/'out/CELLS.md').write_text('Admitted rows after eval-room refusals; target is 50 in every cell. Deficit = 50 minus the displayed value. Exact before/refused/after counts are in CHECKS.json.\n\n'+'\n'.join(cell_lines)+'\n')
gate_path='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/GATE_CAMERA_CALL_RATE_V1.md'
commands={
 'classification_build_shared_grammar':R.PREFIX+'work/build.py',
 'qid_coverage_upstream':R.PREFIX+'work/rebind.py',
 'native_intake':R.PREFIX+'work/intake.py',
 'answers_wording_cells_read40':R.PREFIX+'work/verify.py',
 'source_forms':R.PREFIX+'work/source_forms.py',
 'grammar_boundary':R.PREFIX+'work/grammar_notes.py',
 'room_audit':R.PREFIX+str(BASE/'sb_auditfix2/store_room_audit.py')+' --store '+build['rows']['path']+' --tree '+str(TREE)+' --lists '+str(BASE/'sb_auditfix2/inputs/lists')+' --out '+str(ROOT/'out/room_audit'),
 'final_integrity':R.PREFIX+'work/finalize.py',
 'archive':R.PREFIX+'work/package.py'}
capture(seen)
check=write('out/CHECKS.json',dict(status='PASS_WITH_EVAL_EXCLUSIONS',rows=build['rows'],row_count=5979,native=intake['aggregate'],remaining_refusal_counts=intake['reasons'],remaining_refusals=intake['refusals'],types=build['types'],original_grammar_refusals=classification['refusals_by_reason'],rewrite_rows=edits['rows_by_rule'],changed_rows=build['changed'],unchanged_rows=build['unchanged'],qid_bindings=5979,independent_coverage_entries_unchanged=5979,full_envelope_limit2000=intake['first2000'],shards=intake['shards'],unchanged_fields_rows=verify['only_authorized_field_changes'],printed_response_gt_recomputed=5979,gt_failures=[],room_audit=dict(pin=pin(ROOT/'out/room_audit/audit.json'),hits=audit['hits'],unresolved_rows=0),heldout=dict(reworded_items=450,original_twins=450,threshold=verify['wording_threshold'],normalization='Unmodified sb_rowA build_camera.normalized and fast_wording.near',actual_wording_hits=0,instantiated_template_hits=0,registered_set_hashes_match=True),cells=verify['cells'],cells_short_of_50=verify['cells_short_of_50'],source_base_subset=dict(rows=source['source_rows'],forms=source['forms'],grammar_refusals=source['grammar_refusals'],full_P_base='MISSING locally, as stated in task; only the authenticated 6,000 source rows are measured'),read40=sample['read40'],read40_count=40,grammar_cases=len(grammar['cases']),tree_seal=seal,tree_dependencies_rehashed=sum(Path(p).is_relative_to(TREE) for p in inputs),input_files_rehashed=len(inputs),gate_document=dict(path=gate_path,sha256='MISSING',reason='The authorized one-time read captured text but not the file-byte hash; no second NFS read was performed. Numerical checks rely on separately verified local set pins.'),commands=commands,production_scope='CPU row/envelope validation only. The tree owner must bind/reseal the changed camera source, membership/config/extent-source pins as required by the production composition contract. No production training, frame raster read, or tree modification.'))
report=[
'Camera wording packet: **PASS with eval-room exclusions**. All 5,979 rows pass the pinned shared grammar; native intake admits 5,143 and refuses 836 `excluded:eval_rooms` rows.',
'The full envelope ran at `limit=2000`; disjoint shards of 2,000 / 2,000 / 1,979 rows cover the complete file. No other refusal remains.',
'By type, admitted/refused: displacement 1,717/277; rotation 1,722/271; direction 1,704/288. The 280 exposed exclusions in the input become 836 because grammar failures masked 556 further eval-room overlaps.',
'All 3,977 grammar refusals come from two forms: 1,993 rotation convention lines (`unit_quantity`) and 1,984 direction score lines (`number_not_allowed,unit_quantity`). CLASSIFICATION.json retains every exact line and diagnostic.',
'CAM-ROT-WORDS-v1 replaces the numeric wrap/half-turn convention with the shortest signed turn, positive for left, and a positive half-turn tie. CAM-DIR-SYMBOL-v1 removes only the numeric restatement after a negated component, e.g. `backward = -dz = 0.68 m` becomes `backward = -dz`.',
'The uniform rules edit 1,993 rotation and 1,988 direction traces: 3,981 changed and 1,998 unchanged. Four already-passing direction rows share the edited form. Calls, response bytes and values, questions, options, answers, GT, and all other substantive fields remain unchanged; response offsets are regenerated.',
'GRAMMAR.md states the exact number/unit rules. Numeric provenance can come from printed responses, question constants, valid frames/labels/lists, or verified binary arithmetic. Unit quantities require a matching response value or the result occurrence of correct arithmetic. A symbolic negation alone does not license a numeric restatement.',
'All 5,979 answers and GT labels are recomputed from printed responses and agree. Native replay, per-QID digests, source admission/lineage hashes, and the unchanged independent coverage entries pass.',
'All 450 reworded held-out items and their original twins match registered pins. The unchanged sb_rowA filter finds zero training wording hits below normalized Levenshtein distance 0.20, against both actual held-out questions and all 24 instantiated templates.',
'Room audit: R0=0, dev-S1=0, BENCH=0, withheld-80=0, K1=0; unresolved rows=0. This audit is separate from the native eval_rooms exclusion list.',
'READ40.md prints 40 complete before/after targets across all types, both edit forms, and unchanged cases; it includes questions, options, answers, GT and printed-response recomputation.',
'Both forms occur in P-source extracts: 2,000 rotation and 2,000 direction lines among 6,000 authenticated CAMERA_SOURCES rows. Unchanged source traces and edited wording traces therefore differ in prose. The full P routing base is MISSING locally; no global base counts are claimed.',
'Admitted counts per type × wording follow. Target=50 per cell; every cell below 50 is short by `50 − count`. CHECKS.json also records counts before exclusions and each refusal deficit.',
'',*cell_lines,'',
'Commands producing all numbers (from this workspace): prefix Python commands with `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B`.',
'`work/build.py`: row/form/edit/shared-grammar counts. `work/rebind.py`: digest, coverage and exclusion accounting. `work/intake.py`: full-envelope and shard admission/refusal counts, using execute/tree_reads copied unchanged from fbp_route.',
'`work/verify.py`: unchanged fields, printed GT, held-out distance, cells and READ40. `work/source_forms.py`: source authentication and line-form counts. `work/grammar_notes.py`: six provenance boundary cases.',
'`/scratch/jjyeung/orch_n30/sb_auditfix2/store_room_audit.py --store "$PWD/out/rows/camera_wording.jsonl" --tree /scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1 --lists /scratch/jjyeung/orch_n30/sb_auditfix2/inputs/lists --out "$PWD/out/room_audit"`: room counts; use an empty output directory.',
'`work/finalize.py`: rehashes recorded inputs and checks exact QID/shard/coverage bindings. `work/package.py`: writes and byte-verifies out/fbp_cam.tar; PACKAGE.json records bytes and members. Verify with `sha256sum -c out/fbp_cam.tar.sha256`.',
'Every output JSON carries input SHA256 pins; JSONL rows use BUILD.json and CHECKS.json as companion manifests. The archive includes rows, compressed shards, code, reports and active metadata dependencies; it contains no RGB bytes.',
'Tree seal: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`; grammar: `a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268`. Production composition still requires the tree owner to bind/reseal the changed source and downstream pins. This packet makes no tree changes or training claim.',
'Gate document file-byte SHA256 is MISSING: '+gate_path+'. Its text was read once; the initial read did not capture a hash. The three local held-out/wording files match its registered pins.',
'No-archaeology review: no borderline historical wording is retained. Before/after trace pairs and refusal counts are the requested controlled comparison.'
]
report=[part for i,line in enumerate(report) for part in ([line,''] if i in {0,2,4,6,8,10,11,57,59,61,63} else [line])]
assert len(report)<=80,len(report)
(ROOT/'out/REPORT.md').write_text('\n'.join(report)+'\n')
status(6,'Camera packet passes CPU validation: 5,143 native admissions, 836 eval-room-only refusals, zero grammar/GT/held-out/room-audit failures. All 120 cell counts, 40 trace pairs, exact input hashes and reproducible commands are recorded. Production source resealing belongs to the tree owner; the supplementary gate document byte hash is MISSING.')
print('report lines',len(report),'PASS',flush=True)
