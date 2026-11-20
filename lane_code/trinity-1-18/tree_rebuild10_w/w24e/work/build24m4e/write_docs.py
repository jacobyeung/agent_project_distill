from common import *
iv=J.load(D/'INVARIANTS.json');up=J.load(L/'out/UPLOADS_24M4E.json');hidden=J.load(D/'HIDDEN_PATH_TESTS.json');runs=J.load(D/'TEST_RUNS.json')
assert len(runs)==13 and all(r['returncode']==0 for r in runs)
checks={}
paths=['INVARIANTS.json','UPLOAD_RECONSTRUCTION.json','HIDDEN_PATH_TESTS.json','CATALOG_AUTH_TESTS.json','KIT_TESTS.json','NAMING_TESTS.json','ARM_TESTS.json','ARM_MISSING_DB_TEST.json','ARM_NEGATIVES.json',*['SCAN_'+n+'.json' for n in ('q','n','n_go','qd')],*['guard_'+n+'/'+v+'.json' for n in ('q','n') for v in ('GUARD_TESTS','LEGACY_GUARD_TESTS')],'proofs/resolver600_v2/RESOLVER_TESTS.json','proofs/resolver23/RESOLVER_TESTS.json']
for rel in paths:
 p=D/rel;v=J.load(p);assert v.get('status')=='PASS' or v.get('successful') is True,(rel,v)
 checks[rel]=dict(path=str(p.relative_to(L)),sha256=J.sha(p),status='PASS')
assert 'Ran 7 tests' in (D/'resolver_tests.log').read_text() and (D/'resolver_tests.log').read_text().rstrip().endswith('OK')
checks['resolver_tests.log']=dict(path=str((D/'resolver_tests.log').relative_to(L)),sha256=J.sha(D/'resolver_tests.log'),status='PASS',tests=7)
validation=dict(status='PASS',checks=checks,suites=runs,changed_executable_statements=0,production_admission='NOT_RUN',production_body_availability='NOT_VERIFIED',tree_changed=False,
 fixture_boundaries=['Hidden bwrap view uses authentic receipt and catalog bytes. Only hashes in sealed staging inventories or the authenticated m400 manifest enter the fixture source map. Unavailable production payloads stop native consumers at their pinned-body check. No planner/resolver function is stubbed; checked() is bypassed only for explicitly listed payload boundaries.',
 'All eight hidden r/q checks reach i.refresh -> s1_pool_relocate.relocate -> p3_provenance.pinned for authenticated row member a67a3f6f. This is a local fixture boundary, not a prediction that Orchard lacks the member.',
 'Arming tests run the unchanged helper and complete q planner on a SQLite fixture; unrelated production metadata uses compact fixtures. Guard tests mock GPU queries. Resolver suites use inherited production receipt bytes with explicitly documented payload boundaries.'],
 inherited_only=['Census, VQA replay, live export and review-wait checks from 24m4d; their executable bytes and training configurations are unchanged'],
 readonly_fixture_dependencies=[str(L.parent/'w24/work/build24m3/hidden'),str(L.parent/'w24/work/build24m2c/PIN_AUDIT.json'),str(L.parent/'w24c/work/build24m4c/hidden'),str(L.parent/'ext/m400real'),str(L.parent/'w24/work/build21/resolver21e.py')],
 no_archaeology_borderline_sentences=[])
J.write(D/'VALIDATION.json',validation)
h=hidden['next_boundary']['sha256'];cat=J.load(D/'PINS.json')['pins'][0]['sha256']
replace(L/'out/STILL_MISSING_24M4E.md',f"No further missing staged pin was reached in modes r or q for q, n, n_go or qd. ORCHARD_COPIES_24M4E.json is empty.\n\nThe next local fixture refusal is `Missing or changed pinned input: /tmp/f/payload/{h}` in native pool relocation, at `config.s1_routing.selection.sources.T0_gen_r2.source` (also referenced by P’s catalog). This 29,681,863-byte row member is already authenticated by `k/l.json:staged_inputs.packages.0`; its unavailable body is the inherited fixture boundary. It is not a new missing inventory pin and is not in P’s kit file inventory. Production availability was not checked.\n\nThe catalog’s 181 nested pin references all map to authenticated staging or m400 inventories. Evidence: work/build24m4e/HIDDEN_PATH_TESTS.json.\n")
s=iv['kits'];tree=iv['tree_sha256']
report=[f"Tree {tree}; q {s['q']}; n {s['n']}; n_go {s['n_go']}; qd {s['qd']}.",
 f"Next mode-r fixture refusal: Missing or changed pinned input: /tmp/f/payload/{h}; native pool relocation reaches the inventoried production-body boundary (HIDDEN_PATH_TESTS.json).",
 f"Catalog {cat} (74,599 bytes) is authenticated in all four k/p.json upload inventories and pin_paths; P inventory checksum 2b8242f095c5a8c7… (PINS.json).",
 "All eight hidden r/q checks pass staged-pin closure; no further pin needs binding. ORCHARD_COPIES_24M4E.json is empty; STILL_MISSING_24M4E.md states the body boundary.",
 "Missing-catalog controls name the P.materialization and config.s1_routing fields; wrong catalog hash and size refuse (CATALOG_AUTH_TESTS.json).",
 "Four decoded scans, kit/naming/resolver/guard suites and routing-arming tests pass; only k/p.json and dependent seals changed (VALIDATION.json; INVARIANTS.json).",
 "Tree C, rv.py, arm_routing.py, census, admission, legality, removals, opener rows, step-544 lineage, resolver checks, DEFERRED and b/pc.py remain unchanged.",
 f"UPLOADS_24M4E.json/.list: {up['total_files']} files, {up['total_bytes']} bytes, against 24m3 over 24m2d plus the already-present catalog; u/{cat} is not uploaded.",
 "GO is false except in out/kit_n_go; UPLOADS_24M4E_GO.json is separate and unuploaded. No upload, launch or production preparation/admission ran.",
 "Every original file’s bytes and mode remain in place or attic; disk growth and archive integrity are recorded in DELIVERY_24M4E.json."]
assert len(report)<15
(L/'out/BUILD24M4E_REPORT.md').write_text('\n'.join(report)+'\n')
card=[f"Vehicle N uses MINIMAL on tree C {tree} ({iv['tree_files']} files; work/build24m4e/INVARIANTS.json).",
 f"Kit q {s['q']}; kit n {s['n']}.",f"Kit n_go {s['n_go']}; kit qd {s['qd']}.",
 "GO is false except in out/kit_n_go. The GO delta is separate and has no upload authorization.",
 f"The ordinary upload delta has {up['total_files']} files and {up['total_bytes']} bytes against 24m3 over 24m2d plus the already-present catalog (out/UPLOADS_24M4E.json).",
 f"Stream root: {up['stream_root']}. UPLOADS_24M4E.list contains only files to upload.",
 f"Catalog {cat} is 74,599 bytes and resolves through u/<sha256> in all four kits; Orchard already holds it at x_22c714e1/u/<sha256>, mode 0400 (lane-supplied state).",
 "No additional P-kit copies are required by the tested closure; ORCHARD_COPIES_24M4E.json is empty.",
 f"Both planner modes pass staged-pin closure and reach the fixture’s authenticated row-body boundary {h}; production preparation and admission remain untested (HIDDEN_PATH_TESTS.json).",
 "rv.py uses the native census room authority, including Binding.room when direction twins are enabled; unknown rooms refuse. The protected-room policy and all training configs are unchanged.",
 "Tree C keeps the pointing removal d21e374f as a constant before NAMING_REMOVE. Census, admission, legality, all removals, opener rows, step-544 lineage, resolver identity checks and DEFERRED boundaries remain unchanged.",
 "arm_routing.py reads the current kits, binds the reviewed selection and database metadata, and produces GO=false copies with the already-staged DB excluded from upload bytes. Its semantics are unchanged; real helper and q-planner fixture tests pass (ARM_TESTS.json).",
 "Apply UPLOADS_24M4E before any routing-arming delta. Run out/arm_routing.py from this package with the reviewed selection and db_bytes.json; retain its DB staging prerequisite.",
 "The review wait, census evidence, live publication and b/pc.py checkpoint order are unchanged. All non-executable kit files remain 0644 and executable modes are preserved."]
(L/'out/N_CARD_KIT_ROWS_24M4E.md').write_text('\n'.join(card)+'\n')
print('Validation and reports PASS',flush=True)
