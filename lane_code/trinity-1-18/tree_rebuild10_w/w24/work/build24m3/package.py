from common import *
from storage import growth
import io,tarfile,lzma,gzip,datetime
iv=J.load(D/'INVARIANTS.json');validation=J.load(D/'VALIDATION.json');assert validation['status']=='PASS'
selected={}
def add(p):
 p=Path(p)
 if p.is_file() and not p.is_symlink():selected[str(p.relative_to(L))]=p
for name in ('q','n','n_go','qd'):
 for p in kit(name).rglob('*'):add(p)
for p in (D/'upload').rglob('*'):add(p)
scripts=('common.py','run.sh','storage.py','checks.py','kit_tests.py','naming_tests.py','native_host_tests.py','census_byte_tests.py','census_verified.py','classifier_tests.py','host_review_test.py','delta_sealed_test.py','wrapper_tests.py','wrapper_continue.py','planner_scene_verified.py','scene_tests.py','scene_continue.py','source_pin_tests.py','p_refresh_tests.py','tiny_routing.py','publication_tests.py','regression_tests.py','review_tests.py','live_tests.py','security_tests.py','resolver_tests.py','resolver600_tests.py','resolver23_tests.py','guard_q_legacy.py','guard_q_new.py','guard_n_legacy.py','guard_n_new.py','discovery_census_shell.py','validate_receipts.py')
for name in scripts:add(D/name)
for value in validation['checks'].values():add(L/value['path'])
for name in ('INVARIANTS.json','VALIDATION.json','FINAL_SUITES.json','TREE_VERIFICATION.json','TREE24L4R_SEAL.json','UNCHANGED24L4R.json','HOST24L4R.patch','PROTECTED_ROOMS_API.md','BASELINE.json','PRIOR_PACKAGES.json','POSE_DELTA_LIMITATION.json','SCENE_TIMING.json','POINTING_BINDING.json','BINDING_FINAL_TESTS.json','BINDING_MORE_TESTS.json','CENSUS_BYTE_TESTS.json'):
 add(D/name)
for name in ('q','n','n_go','qd'):
 for suffix in ('.json','.json.gz'):add(D/('SCAN_'+name+suffix))
 add(D/'scanners'/name/'environment_shell21g.json')
 raw=gzip.decompress((D/('SCAN_'+name+'.json.gz')).read_bytes())
 assert hashlib.sha256(raw).hexdigest()==J.load(D/('SCAN_'+name+'.json'))['uncompressed_sha256']
 assert json.loads(raw)['kit_seal']==iv['kits'][name]
for name in ('planner_scene_verified.log','census_final_host.log','host_review_test.log','hidden_delivery.log','checks_delivery.log','delta_sealed_test.log','native_host_tests.log','final_suite_run.log','classifier_tests.log'):
 add(D/name)
add(D/'scene_tests/host.py')
for name in ('RETENTION.json','RETENTION_FINAL.json','RETENTION_ARCHIVES.json'):
 p=D/name;add(p)
 for r in J.load(p)['records']:
  retained=L/r['retained'];assert hashlib.sha256(gzip.decompress(retained.read_bytes())).hexdigest()==r['original_sha256'];add(retained)
for name in ('UPLOADS_24M3.json','UPLOADS_24M3.list','UPLOADS_24M3_GO.json','BUILD24M3_REPORT.md','REMOVAL_RECEIPTS_BLOCKER.md','N_CARD_KIT_ROWS.md','MISSING_STAGED_PINS.md','SCENE_REBUILD_INPUTS.md','TREE_SEAL.json','TREE_FILES.sha256','bind_protected.py','jd.sh','dbb2.py'):
 add(L/'out'/name)
files={n:(p.read_bytes(),p.stat().st_mode&511) for n,p in sorted(selected.items())}
manifest={n:dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=format(mode,'04o')) for n,(raw,mode) in files.items()}
seal=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
target=L/'out'/('tree_rebuild_b24m3_'+seal[:8]+'.tar')
up=J.load(L/'out/UPLOADS_24M3.json');base=J.load(L/'out/DELIVERY_24M2D.json')
inner=dict(schema='build24m3-overlay-v1',status='PACKAGED_WITH_POSE_DELTA_BLOCKER',package=str(target.relative_to(L)),package_seal=seal,base=dict(path=base['package'],sha256=base['sha256']),tree_sha256=iv['tree_sha256'],tree_files=iv['tree_files'],kits=iv['kits'],GO=False,GO_template_upload_authorized=False,checks='PASS',production_admission='NOT_RUN',
 expected_first_discovery_refusal='R1_STAGED_PIN_MISSING:eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9 if absent from authenticated runtime staging; otherwise native reconstruction must first reproduce its complete pinned hash.',
 pointing=dict(sha256='d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1',keys=320,role='protected_rooms',stream='pointing',position=12,expected_source=25020,expected_removed=320,expected_scene_excluded=6584,expected_before_target_shape_filter=18116,expected_K1_heldout_admitted=0,counts_scope='Supplied ORCH expectations, not a local production scan'),
 scene_rebuild=dict(installed=True,native_function='student_pilot.r2_scene_bindings.rebuild',verifier_unchanged=True,original_other_inputs_preserved=True,original_pool_manifest_preserved=True,routing_population='Selected authenticated routing base through native substitution',timing='work/build24m3/SCENE_TIMING.json'),
 receipts=dict(regeneration='Native in-job pool, room audit, scene, stream/target filter, preparation and final identity',census='live/c4.json',row_keys=['live/c0.json','live/c1.json','live/c2.json','live/c3.json'],host='live/h0.json',byte_identical_publication=True,config_identity_and_store_pins_bound=True,source_manifest_authenticated=True),
 discovery=dict(GO=False,census_refusals='WOULD_REFUSE',continues_into_preparation=True,stops_at='WAITING_REVIEW',trains=False,claims='nothing',dbb2_sha256='a7cbfb9f3093ee50bf373838cd952405de190cb8b5dbcc29a0ab0aa1a48d06e5',retry_seconds=60,max_attempts=180),
 delta_tool=dict(path='out/bind_protected.py',binding_staging_resealing_and_upload_diff='BUILT_AND_TESTED',pose_cleaning='BLOCKED_IF_PROTECTED_POSE_ROWS_REMAIN',blocker='out/REMOVAL_RECEIPTS_BLOCKER.md',reason='24l4r has no native producer that filters arbitrary protected pose keys from pose mixtures; existing gates refuse residual rows.'),
 follow_up_tree='24l4s native pointing/VQA fixes remain external; this delivery contains only exact 24l4r. The independent census already checks both pointing resolutions and uses native Binding.room for unresolved VQA.',
 uploads=dict(files=up['total_files'],bytes=up['total_bytes'],stream_root=up['stream_root'],manifest='out/UPLOADS_24M3.json',list='out/UPLOADS_24M3.list',GO_manifest='out/UPLOADS_24M3_GO.json',outside_kit_files=up['outside_kit_files']),
 prior_packages_unchanged=True,prior_package_count=iv['prior_package_count'],disk_cap_bytes=200000000,
 archive_compression='xz; tarfile and GNU tar auto-detect it despite .tar suffix',
 scan_reports='Four gzip JSON reports in work/build24m3/SCAN_<kit>.json.gz; decoded hashes and kit seals are recorded in the adjacent .json files.',
 retained_fixture_evidence='Lossless gzip files and original-byte hashes are embedded with RETENTION*.json; no deletion.',
 archive_sha256_record='External delivery adds the final archive hash, byte count and storage record. Embedded delivery precedes hashing.',
 fixture_boundaries=validation['boundaries'])
record=dict(schema='build24m3-manifest-v1',package_seal=seal,files=manifest,manifest_seal_domain='files only; embedded manifest and delivery excluded',base=inner['base'])
files['work/build24m3/PACKAGE_MANIFEST.json']=((json.dumps(record,sort_keys=True,indent=2)+'\n').encode(),0o644)
files['out/DELIVERY_24M3.json']=((json.dumps(inner,sort_keys=True,indent=2)+'\n').encode(),0o644)
buffer=io.BytesIO();seen={};expected={}
with lzma.LZMAFile(buffer,mode='wb',preset=6) as compressed,tarfile.open(fileobj=compressed,mode='w|') as archive:
 for name,(raw,mode) in sorted(files.items()):
  h=hashlib.sha256(raw).hexdigest();info=tarfile.TarInfo(name);info.mode=mode;expected[name]=dict(sha256=h,mode=mode);key=(h,mode)
  if key in seen:info.type=tarfile.LNKTYPE;info.linkname=seen[key];archive.addfile(info)
  else:seen[key]=name;info.size=len(raw);archive.addfile(info,io.BytesIO(raw))
raw=buffer.getvalue();before=growth()
assert before+len(raw)+1048576<200000000,(before,len(raw))
with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
 actual={m.name:dict(sha256=hashlib.sha256(archive.extractfile(m).read()).hexdigest(),mode=m.mode) for m in archive}
assert actual==expected
for p,h in J.load(D/'PRIOR_PACKAGES.json').items():assert J.sha(p)==h
for name,expected_seal in iv['kits'].items():assert J.seal(kit(name))==expected_seal
with target.open('xb') as f:f.write(raw)
J.write(D/'PACKAGE_MANIFEST.json',record)
delivery=dict(inner,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),verified_members=len(expected),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
J.write(L/'out/DELIVERY_24M3.json',delivery)
J.write(D/'PACKAGE_CHECK.json',dict(status='PASS',members=len(expected),sha256=delivery['sha256'],bytes=len(raw),all_member_bytes_and_modes_verified=True,delivery_embedded=True,decoded_scan_hashes_verified=True,prior_packages_unchanged=True))
final=growth()+1048576;assert final<200000000,final
storage=dict(status='PASS',final_allocated_upper_bound_bytes=final,cap_bytes=200000000,observed_peak_growth_bytes=199565312,pre_baseline_setup_allowance_bytes=65536,observed_peak_with_setup_allowance_bytes=199630848,no_deletions=True,files_deleted=0,method='Distinct inode allocated-block growth from the pre-edit baseline, with a 1 MiB final allowance. Completed fixture archives and reports were retained losslessly. No earlier delivery archive changed.')
J.write(D/'STORAGE_FINAL.json',storage)
delivery.update(final_retained_allocated_upper_bound_bytes=final,final_storage_record='work/build24m3/STORAGE_FINAL.json')
J.write(L/'out/DELIVERY_24M3.json',delivery)
print(json.dumps(dict(package=str(target.relative_to(L)),sha256=delivery['sha256'],bytes=len(raw),members=len(expected),storage_upper_bound=final,status=delivery['status']),indent=2))
