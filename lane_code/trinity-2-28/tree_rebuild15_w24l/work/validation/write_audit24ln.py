"""Write the reviewed comparison inventory with current source locations."""
import ast,json
from pathlib import Path
J=Path(__file__).resolve().parents[2];T=J/'work/tree_r1'
rows=[]
def add(file,needle,comparison,verdict):
    source=(T/file).read_text().splitlines()
    hits=[i+1 for i,line in enumerate(source) if needle in line]
    assert hits,(file,needle)
    for line in hits:rows.append((f'{file}:{line}',comparison,verdict))
H='student_pilot/r1_handover.py';P='student_pilot/r1_persisted.py';C='student_pilot/carrier_c1_run.py'
add(H,"not _same_pin_bytes(source.get('preparation')",'source.preparation versus localized p_run.preparation','CHANGED: N refuses solely on the path. Compare exact pin shapes and SHA256 after pinned(p_run.preparation). test_source_preparation_comparison fails on the base; alternate hash, corrupt bytes and malformed pins refuse.')
add(H,"not _same_pin_bytes(bound.get('preparation')",'binding.preparation versus localized p_run.preparation','CHANGED: same path-only mismatch, independently tested by test_binding_preparation_comparison; schema and config identities remain exact.')
for needle,label in [("stream.get('database') != receipt.get('database')",'prepared database versus donor stream receipt database'),("value.get('division') != receipt.get('division')",'prepared mix division versus donor receipt division'),("part.get(k) != source[k]",'prepared mix source fields, including receipt/model/teacher/plan pins'),("child.get('database') != part.get('database')",'child donor database versus prepared mix database'),("stream.get('receipt') != receipt_pin",'prepared donor stream receipt versus source config stream pin')]:
 add(H,needle,label,'UNCHANGED: both operands come from authenticated donor bytes; pl.localize changes N config pins, not donor file contents. No path-only N mismatch.')
add(H,"complete.get('binding') != bound",'checkpoint binding dictionary, including preparation','UNCHANGED: both authenticated donor records; step-400 export-only N skips the checkpoint branch.')
add(H,"artifact != load(pinned",'artifact dictionary, including nested pins','UNCHANGED: compares the same authenticated artifact bytes; relocation changes the reader path only.')
for needle,label in [("pin_values(setting) !=",'optimizer metadata including nested pins'),("pin_values(a) !=",'shared config fields including nested pins')]:
 add(H,needle,label,'UNCHANGED: already compares pin content identities. No new relaxation of configuration semantics.')
add(H,"if actual != target:",'donor boundary versus target boundary','UNCHANGED: config/store/row-plan digests, not localized whole pins; any difference needs the exact handover mapping.')
add(H,"if mapping != dict",'complete handover map','UNCHANGED: generated for the localized target; source/target values contain identities and store hashes, not read paths.')
for needle,label in [("cfg.get('preparation') != pins['preparation']",'donor cfg.preparation and donor binding.preparation versus receipt.pins.preparation'),("artifact.get(key) != pins.get(key)",'artifact heads/full_weights versus receipt pins'),("stream['receipt'] != cfg['streams'][name]",'prep stream receipt versus donor config; receipt stream pin versus prep stream receipt'),("pins.get(label) != stream['indices']",'receipt index pin versus prepared index pin')]:
 add(P,needle,label,'UNCHANGED: pins here are receipt.pins from the authenticated handover, not localized p_run. All operands retain donor paths. Native relocated-donor fixture passes these checks.')
add(P,"complete.get('binding') != bound",'checkpoint binding versus bound record','UNCHANGED: donor records; skipped for N step-400 export-only initialization.')
add(P,"pins.get(key, {}).get('sha256') !=",'receipt pins versus supplied p_run and artifact','UNCHANGED: already SHA256-only; read() hashes resolved files before JSON reads.')
add(P,"pins.get(label,{}).get('sha256') !=",'checkpoint file pins versus closure','UNCHANGED: already hash-based; N step-400 has no checkpoint state.')
add(P,"pins[label]['sha256'] !=",'export manifest member pins versus closure','UNCHANGED: already hash-based; sizes and safe names remain checked.')
# Fresh preparations bind the already-localized configuration; the kit synchronizes host/review additions.
for needle,label in [("receipt.get('r1_training') != cfg.get('r1_training')",'preparation r1_training dictionary (all nested pins)'),("receipt.get('r2_sampling') != cfg.get('r2_sampling')",'preparation sampling dictionary (card/population/indices)'),("receipt.get('s1_route_policy') !=",'preparation frozen-policy dictionary (table pin)'),("receipt.get('remove_files', []) !=",'preparation removal pin list'),("receipt.get('ground_target_filter') !=",'ground-target filter settings (including any nested pins)'),("{k: v['receipt'] for k, v in receipt['streams'].items()} !=",'prepared stream receipt pins versus config streams'),("receipt.get('depth_init') !=",'preparation depth-init pin versus config'),("source['database'] != value['database']",'source receipt database versus prepared database'),("review.get('preparation') != cfg['preparation']",'independent C1 admission preparation pin')]:
 add(C,needle,label,'UNCHANGED: q creates preparation after localization and bind_prepared/bind_handover preserve it; h.py and rv.sync_preparation synchronize host/review pins before u.py. Source database pins retain authenticated receipt paths. No kit-only relocation between these operands. C1 admission is a separate review check.')
for needle,label,reason in [("receipt.get('b7_inputs') !=",'prepared b7_inputs dictionary','N has no b7_inputs'),("receipt.get('mdg') !=",'prepared mdg dictionary','N has no mdg'),("{k: receipt['validation'].get(k)",'prepared validation rows/slice pins','N has no validation'),("value['indices'] != source['dense_indices']",'paired-prefix index pins','N uses duplicate frames, not paired-prefix preparation'),("receipt.get(k) != cfg.get(k) for k in POSE_ONLY_RECEIPT_KEYS",'pose-only prepared settings, including pins','N training_mode is final')]:
 add(C,needle,label,'UNCHANGED: '+reason+'.')
for needle,label in [("parent['database'] != receipt['source_database']",'paired-prefix parent/source database'),("parent[k] != receipt[k]",'paired-prefix settings/inputs/model'),("stream['receipt'] != receipt['parent']",'paired-prefix receipt/parent and database/parent database'),("stream['indices'] != receipt['dense_indices']",'paired-prefix dense indices'),("readout != bound_readout",'paired-prefix readout dictionary including pins')]:
 add(C,needle,label,'UNCHANGED: paired pose-only preparation; inactive for N final/duplicate configuration.')
add(C,"stream_division == pose_division",'stream division versus pose division','UNCHANGED: prepare/build derive these pins from authenticated stream receipts, not cfg.scene_division; both retain producer paths. Ancestor fallback retains its existing scene semantics.')
add(C,"child.get('parent_division') != pose_division",'division parent link versus pose division','UNCHANGED: authenticated division-link pins; not localized by pl.py. Scene legality stays byte-identical.')
for needle,label in [("gate.get('artifact')!=file_pin",'milestone artifact pin versus local published artifact'),("pose.get('artifact') != gate['artifact']",'readout artifact versus milestone gate artifact'),("pose.get('contiguous_clips') != clip_pin",'readout clip pin versus gate clip report')]:
 add(C,needle,label,'UNCHANGED: N milestone_gate is null and gate_stop is false; later milestone products use their own published paths, not localized P pins.')
# Train/checkpoint helpers carry local N bindings, or are inactive resume/export/geometry modes.
for needle,label in [("old[k] != bound[k] for k in ('preparation', 'world_size')",'export binding preparation/world'),("cfg.get('code') != old_cfg.get('code')",'current versus old config code pin'),("receipt.get('binding') != bound",'binding-history receipt versus binding'),("manifest['binding'] != bound",'checkpoint manifest versus binding'),("previous != bound",'existing output binding versus current binding'),("output_bindings(directory.parent)[-1][0] != bound",'checkpoint output binding versus bound'),("meta['base_artifact'] != file_pin",'existing export base artifact pin'),("b != expected_binding",'attempt binding versus expected binding'),("attempt.get('binding') != expected_binding",'checkpoint attempt binding'),("report['binding'] != expected_binding",'checkpoint rank report binding'),("attempts[key]['binding'] == manifest['binding']",'checkpoint owner binding'),("attempts[owner]['binding'] == manifest['binding']",'checkpoint owner binding'),("bound['preparation'] != preparation",'geometry reference preparation'),("reference_cfg['streams'] != cfg['streams']",'geometry reference stream pins'),("export_binding['preparation'] != bound['preparation']",'export-only resume binding preparation')]:
 add(C,needle,label,'UNCHANGED: N u.py calls train(cfg) without resume/export binding and without geometry_online. Fresh output bindings/checkpoints use N local preparation; resumed/history checks compare their own published records, not localized P preparation.')
for needle,label in [("normalize(load(pinned(pin)).get('component_evidence', {})) != status",'component-evidence records versus normalized statuses'),("normalize(records) != status",'component registry records versus artifact statuses'),("recorded != status",'component preparation evidence versus artifact statuses')]:
 add('student_pilot/r1_components.py',needle,label,'UNCHANGED: authenticated evidence/status comparison, not a pin-to-localized-pin comparison. N records derive from its own prepared config; inherited donor evidence stays in donor bytes. DEFERRED boundary unchanged.')
add('student_pilot/r1_population.py',"!= {k:v for k,v in original.items()",'reader-filter stream dictionaries including nested pins','UNCHANGED: bind_prepared deep-copies the preparation; scene_receipt compares that copy against its own reader_source, excluding only selection/count fields. No localization occurs between them.')
add('launch_r1/p_opener_witness.py',"artifact['routing_vocabulary'] != recorded",'recorded vocabulary versus prepared vocabulary','UNCHANGED: vocabulary values are schema/hash/size/openers, not paths. Metadata pins are read through pinned; donor comparison is the changed _donor above.')
# Related q helpers were inspected as well.
for needle,label in [("proof.get('database')!=actual",'twin receipt database and binding pins'),("proof.get('source_database')!=spec['source_database']",'twin receipt source_database and rows pins')]:
 add('student_pilot/r1_direction_twins.py',needle,label,'UNCHANGED: augment writes the receipt from the localized spec and new database; verify_augmented reads those same pins.')
add('student_pilot/r1_coverage.py',"spec['union']!=pin",'K1 union spec versus configured removal pin','UNCHANGED: both pins belong to N config and are localized together; exclusion content checks remain exact.')
for needle,label in [("pin_values(pin) !=",'deferred routing request pin versus config'),("pin_values(base) !=",'routing base versus config')]:
 add('student_pilot/r1_coverage.py',needle,label,'UNCHANGED: already compares hash identities; existing pinned reads remain in place.')
for needle,label in [("division_pin == ancestor_pin",'ancestor division equality'),("parent_pin == ancestor_pin",'ancestor parent-link equality')]:
 add('student_pilot/c1_pose_mix.py',needle,label,'UNCHANGED: division ancestry operands come from authenticated receipts; N localization does not rewrite those bytes. No scene-admission predicate changed.')
add('student_pilot/s1_admission.py',"load(output / \"request.json\") != request",'preparation request dictionary including config pin','UNCHANGED: same-root retry guard; q starts fresh, so N does not hit it with localized old request bytes.')
add('student_pilot/s1_admission.py',"load(output / \"data_receipt.json\") != data_receipt",'data receipt dictionary with nested pins','UNCHANGED: compares products of the same local preparation. No localized donor pin operand.')
add('student_pilot/s1_admission.py',"existing.get(\"config\") != prepared[\"config\"]",'existing resume config and source-seal pins','UNCHANGED: non-prepare-only resumed audit; q calls prepare_only=True.')
for needle,label in [("cfg.get(k) != receipt.get(k) for k in ('r1_training'",'opener start-config metadata including init/vocabulary pins'),("cfg.get('streams') != {k:v['receipt']",'opener start-config stream pins')]:
 add('student_pilot/r2_openers.py',needle,label,'UNCHANGED: prepared() attaches the same final local config as _r1_start_config; h.py/rv synchronize host/review changes. No second localization occurs.')
for needle,label in [('receipt.get("dev_scene_exclusions") != pin','prepared dev exclusion pin'),('receipt.get("benchmark_scene_exclusions") != benchmark_pin','prepared benchmark exclusion pin'),("value != expected",'scene-filtered stream metadata dictionary'),('receipt.get("scene_filter_report") != coverage_report','scene-filter report including input pins')]:
 add('student_pilot/s1_exclusions.py',needle,label,'UNCHANGED: preparation creates these values from the localized cfg and authenticated original stream receipts. Exclusion membership, predicates and accounting remain exact.')
for needle,label in [("value['files'] != rule.files",'scene-rebuild dev/benchmark pins and coverage dictionary'),("reference.get('withhold_file') != rule.files['dev']",'scene-reference dev pin'),("reference.get('benchmark_file') != rule.files['benchmark']",'scene-reference benchmark pin'),("counts.get('merged_dev') != rule.files['dev']",'legacy mixture-count dev pin and sampling counts pin')]:
 add('student_pilot/r2_scene_bindings.py',needle,label,'UNCHANGED: supplied N k/c.json and k/n.json set r2_scene_rebuild and scene_coverage to null, despite r2_all_stream_exclusions=true; z.resolve/pl do not populate them. Native prepare would fail pinned(None) before these comparisons. This is missing evidence, not a demonstrated path-only mismatch. N has no r2_build2; counts branch is inactive. If scene receipts are supplied, their localization requires a separate authenticated fixture audit.')
add('student_pilot/r2_scene_bindings.py',"spec['rows'] != old.get",'source-rebuild raw metadata pin versus source receipt','UNCHANGED: scene-rebuild producer, not called by supplied q/u entrypoints. Missing scene evidence cannot be fixed by weakening this binding.')
add('student_pilot/r1_absence.py',"if actual!=entry",'absence record dictionary including builder/inventory pins','UNCHANGED: official evidence verification; inherited DEFERRED prevents unsupported claims. Fresh N absence records use the same runtime builder and authenticated inventory; no affected localized config pin.')
add('student_pilot/r2_policy.py',"catalog_pin != policy.get('catalog')",'provided catalog versus policy catalog pin','UNCHANGED: optional policy/preparation catalog argument; N uses r1_training components without r2_build2 catalog override.')
for needle,label in [('receipt["exclusions"] != pool.files','pool exclusion lists and scene-exclusion pins'),('receipt["source_scene_exclusions"]["files"] != pool.scenes.files','pool scene-report input pins'),('receipt["source_scene_exclusions"]["expected"][name] != expected_scene_counts','pool scene census including source and membership pins')]:
 add('student_pilot/s1_pool.py',needle,label,'UNCHANGED: s1_routing.build calls s1_pool_relocate.relocate, which rewrites these generated receipts together before selected_rows reads them. No one-sided localization.')
add('student_pilot/s1_pool_relocate.py',"result != pin",'relocated pin versus recorded pin','UNCHANGED: only records a move; not an admission equality. pinned(result) authenticates the chosen bytes.')

# Write explicit rows for entrypoints without a direct whole-pin equality.
rows.extend([
('launch_r1/production_proof.py:_run,bind_handover','No direct whole-pin equality','UNCHANGED: staged pins are rehashed, then donor/compare_configs perform comparisons listed above; bind_handover writes the final local receipt/config.'),
('student_pilot/r1_handover.py:bind_target','No direct whole-pin equality','UNCHANGED: delegates to donor and compare_configs, then writes an exact mapping for the localized target.'),
('student_pilot/r1_persisted.py:admission','No direct whole-pin equality','UNCHANGED: delegates to verify and training.start under verified relocation scope.'),
('student_pilot/r1_population.py:bind_prepared','No direct whole-pin equality','UNCHANGED: prepared() checks the local preparation; bind_target performs donor binding.'),
('launch_r1/entry.py:admit,stage_host','Host/review identity digests; routing_substitution diagnostic compares pins','UNCHANGED admission. The new substitution boolean records a difference without refusing it; selection digest computation/comparison stays exact.'),
('in24kr/kit_n_go/b/u.py:14','identity(cfg) versus identity(q config)','UNCHANGED: h.py/rv add host/review with preparation synchronization, which identity excludes. u.py does not relocalize q output.'),
('in24kr/kit_n_go/b/h.py:20','host receipt path versus q/host.json','UNCHANGED: checks the local q output, not a donor pin. Its path remains fixed.')])
resolved=[]
for location,comparison,verdict in rows:
    if location.startswith('in24kr/') or location.rsplit(':',1)[-1].isdigit():
        resolved.append((location,comparison,verdict));continue
    filename,names=location.split(':',1)
    for name in names.split(','):
        for number,line in enumerate((T/filename).read_text().splitlines(),1):
            if line.startswith('def '+name+'('):
                resolved.append((filename+':'+str(number),comparison,verdict))
rows=resolved
lines=['Only the two donor preparation comparisons change. Every other comparison below retains its existing semantics.',
'Inputs: decoded kit k/c.json, k/n.json, k/p.json, k/r.json, k/h.json; in24kr/REHEARSAL_K_BINDING_EVIDENCE.json; pl.py localization and h.py/rv.py/u.py publication flow.',
'The evidence records preparation a5bbef1b, config identity 9459724f and schema c1-preparation-v1 on both sides; only the preparation paths differ. Production files were not read or executed.',
'Whole dictionaries/lists containing pins are included. Scalar schema/step/count/hash checks are retained; PIN_AUDIT_CANDIDATES.json records the broader expression scan.',
'For BOTH changed comparisons, r1_handover._donor reads preparation with load(pinned(pins["preparation"])) before comparing it; pinned hashes the resolved file before load reads it. r1_persisted.verify additionally hashes the staged preparation before its binding checks.',
'', '| Location | Comparison | N localization verdict / action |','| --- | --- | --- |']
lines += ['| '+' | '.join(v.replace('|','\\|').replace('\n',' ') for v in row)+' |' for row in rows]
lines += ['', 'Hash-verification locations (current tree):']
for f,needle in [(H,"preparation = load(pinned(pins['preparation']))"),('student_pilot/p3_provenance.py',"sha256(path) != pin['sha256']"),(P,"sha256(path) != pin['sha256']"),(P,"records = {k:load(read(k))")]:
 for i,line in enumerate((T/f).read_text().splitlines(),1):
  if needle in line:lines.append(f'- {f}:{i}: `{line.strip()}`')
lines += ['', 'Tests: DonorPins.test_source_preparation_comparison and test_binding_preparation_comparison independently pass same SHA at another path, refuse another correctly hashed preparation, and refuse wrong localized bytes with the old SHA. Both reproduce P_EXPORT_RUN_BINDING_MISMATCH on the base.',
'DonorPins also tests native persisted verification, schema/config-identity mismatches and malformed pin fields. LocalizedQ reaches native bind_target, final bind_handover, persisted admission and loader-audit control flow in q-proof and fresh-training modes. Capacity preparation/population/loader and opener production are fixture stubs; no real training or launch PASS is claimed.']
(J/'out/PIN_COMPARISONS_24N.md').write_text('\n'.join(lines)+'\n')
print('Comparison rows:',len(rows))
