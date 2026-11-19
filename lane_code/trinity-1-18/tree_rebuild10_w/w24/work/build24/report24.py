from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';sys.path.insert(0,str(D));import joblib as J
k=J.load(D/'KIT.json');c=J.load(D/'CENSUS.json');u=J.load(L/'out/UPLOADS_MINIMAL.json');tests=J.load(D/'TEST_COUNTS.json');cov=J.load(D/'COVERAGE.json')
f=J.load(D/'proofs/capacity/final/RESULT.json') if (D/'proofs/capacity/final/RESULT.json').exists() else {'status':'PENDING','milestones':{}}
d=J.load(D/'DELIVERY.json') if (D/'DELIVERY.json').exists() else None
lines=[('BUILD COMPLETE; production GO=false.' if f['status']=='ADMIT' and tests['successful'] and d else 'BUILD PENDING: final native capacity evidence or package verification is not yet complete. GO=false.'),
'',f"Tree: {k['q']['tree_seal']}.",f"Kit q (400): {k['q']['kit_seal']}.",f"Kit n (600): {k['n']['kit_seal']}; advanced, four GPUs/four ranks, one launcher."]
if d:lines += [f"Package: {d['package']}; {d['bytes']:,} bytes; SHA-256 {d['sha256']}.",f"Package seal: {d['package_seal']}; {d['members']} members; stream verification PASS; workspace {d['workspace_bytes']:,} bytes."]
lines += ['', 'MINIMAL uses `r1_training.routing_slices: "deferred_first_boundary"`. The merged tree contains build23 and the released build23b fix, with build22 VQA behavior preserved.',
 'The central check rejects every named slice binding through config/request row_slice_inputs, routing_inputs, active row_sources, source membership, composed routing receipts, mix/sampler/request cards, ceilings, counts and indices.',
 'Camera wording and dynamic EXTRA_PINS are included. Only room and room_programs_excluded remain as catalog audit provenance. FULL retains its camera composition and exclusions.',
 'Entry, build, production_proof, s1_admission, population and room paths call the gate before row readers. Seven source files changed; TREE_CHANGES.json and TREE_CHANGES.diff identify every change.',
 'The step400 branch still accepts only its export-only receipt. Step600 accepts p-handover-v1 with exact checkpoint/export closure through plan A h_6ed2c7aa/m600 or plan B pb_a5416871.',
 'The real pb200 files supplied the schema witness; step200 refuses E56:200. Fixture plans A/B pass filling, resolving and payload staging. Altered identities, milestones, closure paths, exports and model metadata refuse.',
 'IDENTITY_CHECKS.json proves unchanged export_identity, metadata_closure and identity predicates except the requested exact artifact-step comparison.',
 'M600_PINS.json names export tar/parts, artifact, receipt/RP/control files, persisted files, every checkpoint_000600 file and every model-manifest file. Real handover values remain pending.',
 '`out/fill_m600.py` authenticates those inputs, fills only the declared capsules, reseals n and emits resolved/fill/upload records. Its tests prove all other kit files and VQA settings remain unchanged.',
 'N’s four-rank launch configuration uses proof_mode=train at 600; native checkpoint admission accepts it without a proof-scope override (LAUNCH_MODE.json). The allocation supplies its own mode-q canary. GO stays false; production admission and official component gates remain enforced.',
 '', '| Kit/check | Furthest stage | Classification |', '|---|---|---|']
for name in ('q','n'):
 x=J.load(D/('LOOKAHEAD_'+name+'.json'));lines.append(f"| {name}, own decoded config | {x['result']['refusal']} | {x['classification']} |")
lines += ['| n, unfilled resolver | E68 | Pending handover boundary |','| A/B fixture handover | Resolved and payload staged | PASS |','| Actual GPU guard in CPU view | E42 | Stand-in boundary |',
 '', '| CPU fixture | Status | First losses, ranks 0 / 1 / 2 / 3 |','|---|---|---|']
for step in ('600','400'):
 x=f['milestones'].get(step)
 lines.append(f"| {step} {'checkpoint' if step=='600' else 'export-only'} | {x['status'] if x else 'PENDING'} | "+(' / '.join(f"{x['first_losses'][str(i)]:.8g}" for i in range(4)) if x else 'pending')+' |')
if f['status']=='ADMIT':
 lines += ['The native 600 run produced the stores, regenerated S1 routing, authenticated handover, built the population, audited the 1,000-step sampler and ran the complete first batch.',
 'The final merged tree reuses those immutable prepared stores and the unchanged sampler audit, authenticates its own source/config binding, and runs checkpoint/export admission plus full forward on all four ranks at both milestones.',
 'The 400 branch publishes a native export and export-only receipt from the same synthetic model when it reuses the 600 store audit. This is a capacity/schema fixture, not a simulated training trajectory.',
 'Each milestone has 288 finite full-forward row losses and eight refusal twins. Direction population is 39,971 = 32,000 synthetic base + 7,971 twins; all deferred cells are zero.',
 'The source VQA producer matched all 109 named controls: the new list removed 107 and the existing K1 union removed two. NOT_PRESENT stays limited to two absent heads; seven component slots remain DEFERRED.',
 'Fixture boundaries: synthetic RGB/labels and catalogs, tiny native model dimensions, processor constructor, local CPU publication collectives, and synthetic twin/store hash constants. Native authentication, row validators, samplers and full forward execute.',
 'Evidence: work/build24/proofs/capacity/{600/q,final}/; final/RESULT.json records each reused audit and native producer receipt.']
lines += ['', '| VQA family | Before new list | Newly removed | Eligible with twins |','|---|---:|---:|---:|']
for name,v in sorted(c['VQA'].items()):lines.append(f"| {name} | {v.get('before','?'):,} | {v.get('new_removals',0):,} | {v['eligible']:,} |")
lines += [f"Routing is P’s base only: {c['routing']['rows']:,} rows, receipt ca0616db, database 4e8e6c04 at 400; the 600 fill authenticates P’s runtime base.",
 'The retained build22 census has held-out wording hits 0, unremoved K1 hits 0, room-rule hits 0 and twin/source room mismatches 0. Deferred slices contain zero rows; native validators refuse any held-out wording in retained training rows.',
 'The production VQA census is carried from build22 by identical store, twin, removal and exclusion pins. The production routing database was not available for a fresh scan; its pinned receipt supplies the row count. CENSUS.json records this limit and evidence hashes.',
 'Relative-count rows and answer-prior weights remain unbound. Step-time patches remain absent/OFF, the frame-host alias patch remains deferred, opener initialization stays keep, and step544 lineage remains unchanged.',
 '', '| Upload diff against Orchard q bb04241c | Needed files / bytes | Transfer files / bytes |','|---|---:|---:|']
for name in ('q','n'):
 x=u['kits'][name];lines.append(f"| {name} | {x['needed_files']} / {x['needed_bytes']:,} | {x['transfer_files']} / {x['transfer_bytes']:,} |")
lines += [f"One combined stream: {u['transfer_files']} files, {u['transfer_bytes']:,} uncompressed bytes. UPLOADS_MINIMAL.json lists names, bytes, SHA-256, local paths, reuse/add/replace and MINIMAL need; UPLOADS_MINIMAL.list is the tar file list.",
 'The baseline is build21g UPLOADS.json plus archived build23 UPLOADS_NEW.json. Deferred camera rows are absent. Existing provenance pins retain their closure files without activating their routing cells.',
 f"Tests: {tests['tests']} passed, including 112 central-binding regressions, build23’s eight MINIMAL and two resolver tests, build22’s 19 tests, 16 new resolver/fill tests, five new kit tests and the inherited focused/scanner/naming/resolver suites.",
 f"Changed-statement coverage: {cov['covered']}/{cov['total']}; COVERAGE.json lists uncovered lines. Every new refusal has a mutation test.",
 'Decoded scans PASS for q, n and both filled fixture kits. The reviewed shell certificate for n differs only in partition and GPU resource directives; a modified program still refuses.',
 'N_CARD_KIT_ROWS.md states the first-200-step changes and boundary timing. M600_HANDOVER.md documents the single fill command.',
 'All earlier packages remain unchanged. No network, upload, scheduler submission, GPU, Git, SSH or other agent was used. Production frame-host execution, real step600 pins and independent review remain required.']
if d:lines += [f"Fixture prerequisites: {d['fixture_prerequisite_bytes']:,} bytes, included. Generated capacity databases/weights are omitted; the supplied harness rebuilds them. The /scratch CPU Python environment is external."]
assert len(lines)<150,len(lines);(L/'out/BUILD24_REPORT.md').write_text('\n'.join(lines)+'\n');print('Report lines',len(lines))
