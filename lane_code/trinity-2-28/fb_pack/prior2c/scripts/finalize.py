"""Write the host contract, regression summary, concise report and authenticated package."""
import argparse,hashlib,json,os,shlex,sys,tarfile
from pathlib import Path
W=Path(__file__).resolve().parents[1];FB=W.parent;OLD=FB/'prior2b';inputs={}
PY='/scratch/jjyeung/envs/p1cpu/bin/python'
PREFIX='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 '+PY
def pin(p):
 p=Path(p).resolve();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 v=dict(path=str(p),sha256=h.hexdigest());inputs[str(p)]=v;return v
def load(p):pin(p);return json.loads(Path(p).read_text())
def put(p,v):
 p.write_text(json.dumps(dict(v,inputs=list(inputs.values())),sort_keys=True,indent=2)+'\n');return pin(p)
def host_inputs():
 pin(__file__)
 original=load(OLD/'out/HOST_INPUTS.json');launch=load(W/'out/N_LAUNCH_CONFIG.json')
 for p in [FB/'priorrev/REVIEW_VERDICT.md',W/'out/prove_on_prepared.py',W/'out/run_on_host.py',
           W/'out/TOWARD_HARD_WEIGHTS.json',W/'out/PATCH_PRIOR.patch',
           OLD/'work/sealed_new/student_pilot/r1_population.py',OLD/'work/sealed_new/student_pilot/r1_training.py',
           OLD/'work/sealed_new/launch_r1/production_proof.py',OLD/'work/sealed_new/launch_r1/entry.py']:
  pin(p)
 source_stores=original['source_stores_missing']
 source_checks={
  'pointing':'receipt.streams.pointing.database; also source_receipt.database',
  'pose':'receipt.streams.pose.sources[*].database in launch order; also each child receipt.database',
  'routing_base':'receipt.streams.routing.database; source receipt.source_scene_exclusions.expected.r16.population.database'}
 for entry in source_stores:
  entry['status']='MISSING';entry['checked_fields']=source_checks[entry['cell']]
  entry['sha256']=entry['pin']['sha256'];entry['expected_location']=entry['pin']['path']
 fields=['streams','r2_sampling','r1_training','config_sha256','source_seal']
 alternatives={
  'b':dict(config='<proof root>/b/config.json',receipt='<proof root>/b/receipt.json',
           producer='launch_r1.production_proof._run -> r1_population.bind_prepared',
           reads={'preparation':'config.preparation.sha256 equals receipt bytes',
                  'prior_policy':'config.r1_training.direction_prior.sha256 equals --weights',
                  'prior_offsets':'config.r2_sampling.direction_prior; receipt.r2_sampling must equal config.r2_sampling',
                  'row_plan':'config.r1_training.row_plan_sha256 equals digest(config.r2_sampling)',
                  'source_identity':'receipt.streams.* databases and receipts; receipt.r1_training equals config.r1_training',
                  'code':'config.code; receipt.source_seal and receipt.config_sha256'}),
  'h':dict(config='<proof root>/h/config.json',receipt='<proof root>/h/receipt.json',
           producer='launch_r1.production_proof.bind_handover',
           reads={'preparation':'config.preparation and receipt fields as for b',
                  'store_hashes':'config.r1_training.store_hashes equals native target_identity(config).stores',
                  'base_vqa':'store_parameter and direction_twins.source_database remain anchored to N v7 210b2534',
                  'sampling':'r2_sampling remains the b binding; offsets/population/indices are read from their pins'}),
  'population':dict(config='<proof root>/population/config.json',receipt='<proof root>/population/receipt.json',
           producer='launch_r1.entry.frame_host -> r1_population.bind_prepared',
           reads={'preparation':'config.preparation and receipt fields as for b',
                  'sampling':'config.r2_sampling points to files under population/'})}
 host=dict(status='MISSING_REAL_PREPARATION',production_gate='MISSING',
  proof_root=dict(status='MISSING',path='MISSING: actual training-host proof root was not supplied'),
  config=dict(path='<proof root>/b/config.json',sha256='MISSING',
              required_fields=['preparation','r2_sampling','r2_sampling.direction_prior','r1_training.direction_prior',
                               'r1_training.row_plan_sha256','r1_training.store_hashes','code']),
  preparation=dict(path='<proof root>/b/receipt.json',sha256='MISSING',required_fields=fields),
  preparation_variants=alternatives,
  launch=dict(pin=pin(W/'out/N_LAUNCH_CONFIG.json'),expected_sha256='0e78d7f86f85cf6090db94bb4916fbd1c57b9fa2aff04dd0a8428a414a4a5f5f',
              store_hashes=launch['r1_training']['store_hashes'],store_parameter=launch['r1_training']['store_parameter'],
              store_parameter_local_status='MISSING: exact e3ee51da launch receipt bytes are not supplied here',
              direction_twins=launch['r1_training']['direction_twins']),
  weights=pin(W/'out/TOWARD_HARD_WEIGHTS.json'),checker=pin(W/'out/prove_on_prepared.py'),
  source_stores_missing=source_stores,stream_receipts=original['stream_receipts'],
  post_filter_tables={s:dict(path='<proof root>/b/'+s+'_'+('order' if s=='pose' else 'indices')+'.json',sha256='MISSING',
                     required_field='receipt.streams.'+s+'.'+('order' if s=='pose' else 'indices'))
                     for s in ('pose','vqa','routing','pointing')},
  population=dict(path='<proof root>/b/population.json',sha256='MISSING',required_field='config.r2_sampling.population'),
  indices=dict(path='<proof root>/b/indices.json',sha256='MISSING',required_field='config.r2_sampling.indices'),
  prior_offsets=dict(path='<proof root>/b/direction_prior.json',sha256='MISSING',required_field='config.r2_sampling.direction_prior',
                     compared_fields=['schema','cells (ordered offsets by cell and side)','policy.sha256','card_sha256','population_sha256','indices_sha256']),
  prior_preparation='Before native bind_prepared, set r1_training.direction_prior to the exact path/SHA256 pin of the packaged weights. Native produce emits r2_sampling.direction_prior in the final config and receipt.',
  vqa_augmentation=dict(receipt='<proof root>/twins/augmentation.json',database='<proof root>/twins/rows.sqlite',status='MISSING',
                        check='Native verify_augmented compares every base row and appended twin against pinned launch sources.'),
  sealed_patched_tree=dict(status='MISSING: final config.code and receipt.source_seal were not supplied',
     required_fields=['config.code (sealed file inventory and archive)','receipt.source_seal','receipt.config_sha256'],
     admitted_pairs=[dict(base='189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710',
                          patched='35a4753f97906fcf7d84d3e9dea4d2f837f5bfa5a274e261aa7c7530f9597f25'),
                     dict(base='57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7',
                          patched='31c8f6b8c28c8213ff78a65df6f0fce23a99c24f56945359dade50d394a6236c')],
     note='Seal the exact patched tree before producing the final config/receipt. A seal naming the unpatched tree fails.'),
  training_host_command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 "$PY" out/run_on_host.py --proof-root "$PROOF_ROOT" --stage b --base-tree "$BASE_TREE" --patched-tree "$PATCHED_TREE" --weights out/TOWARD_HARD_WEIGHTS.json --output-dir "$CHECK_OUTPUT"',
  command_inputs={'PY':'Training-host Python with the native CPU dependencies; this node uses '+PY,
                  'PROOF_ROOT':'MISSING: actual native proof directory',
                  'BASE_TREE':'Exact sealed base matching one admitted pair',
                  'PATCHED_TREE':'Exact PATCH_PRIOR tree matching that pair, including its authenticated source seal/archive',
                  'CHECK_OUTPUT':'A new writable checker output directory'},
  command_notes='Use --stage h for the handover config or --stage population for entry.frame_host. The wrapper reads the selected receipt’s stream receipt and post-filter table pins, prints the complete checker command, and saves HOST_COMMAND.json. Add --pin SHA256=PATH only for identical relocated bytes.',
  transitive_inputs='Every pinned receipt, database, index/order table, membership file, weight file, source archive and imported source file opened by the checker appears with SHA256 in RESULT.json.',
  command=PREFIX+' scripts/finalize.py --host-inputs')
 put(W/'out/HOST_INPUTS.json',host)
 return host

def finalize():
 host=host_inputs()
 groups={name:load(W/'out'/file) for name,file in [
  ('cli','CLI_TESTS.json'),('offsets','OFFSET_TESTS.json'),('trees','TREE_PROVENANCE.json'),
  ('host_wrapper','HOST_WRAPPER_TESTS.json'),('integration','INTEGRATION_TESTS.json')]}
 records=[]
 checker=pin(W/'out/prove_on_prepared.py')
 for group,value in groups.items():
  assert value['status']=='PASS',(group,value['status'])
  recorded={p['path']:p['sha256'] for p in value['inputs']}
  assert recorded.get(checker['path'])==checker['sha256'],('UNTESTED_CHECKER_BYTES',group)
  records += [dict(group=group,**r) for r in value.get('records',[])+value.get('seal_tests',[])]
 for path in sorted((W/'scripts').glob('*.py')):pin(path)
 for path in (W/'out/run_on_host.py',W/'out/prove_on_prepared.py',W/'out/HOST_INPUTS.json'):pin(path)
 summary=dict(status='PASS',production_gate='MISSING',tests=len(records),passed=sum(r['status']=='PASS' for r in records),
   failed=sum(r['status']!='PASS' for r in records),records=records,
   commands={name:PREFIX+' scripts/'+script for name,script in [
    ('cli','test_checker.py'),('offsets','test_offsets.py'),('trees','verify_trees.py'),
    ('host_wrapper','test_host_wrapper.py'),('integration','test_integration.py')]},
   all_prior2b_checker_tests='PASS: duplicate, missing, hash, incomplete, fixture_as_real',
   fixture_plan_sha256=groups['integration']['plan_sha256'],
   fixture_cells=groups['integration']['cells'],fixture_draws=groups['integration']['draws'])
 put(W/'out/TESTS.json',summary)
 counts={k:len(v.get('records',[]))+len(v.get('seal_tests',[])) for k,v in groups.items()}
 report=[
  'The production checker requires the configured prior, authenticates its offsets against native-row recomputation, and runs the unchanged production binding.',
  '',
  'Real mode anchors the source databases to N’s launch config (`0e78d7f8`), including v7 `210b2534`, authenticates native twin augmentation, and verifies the complete patched tree, source archive, and preparation seal. Handover store hashes must match the native final stream identities.',
  '',
  f"All {summary['tests']} regression checks pass: {counts['cli']} CLI checks, {counts['offsets']} offset/identity checks, {counts['trees']} tree/seal checks, {counts['host_wrapper']} host-path checks, and {counts['integration']} native-reader integration checks. TESTS.json records each command, result, and input hash.",
  '',
  'All five prior2b checker tests pass. The reviewer’s exact unlabelled fixture fails with `REAL_LAUNCH_STORE_HASHES_MISMATCH:vqa`.',
  '',
  'The reviewer’s re-pinned facing-side swap and non-target insertion fail with `PRODUCTION_PRIOR_OFFSETS_MISMATCH:cells`. Full CLI regressions also reject both; removing their fixture labels cannot grant a real PASS.',
  '',
  f"The labelled fixture still passes with identical plans, cell results, and audits across {summary['fixture_cells']} cells and {summary['fixture_draws']:,} draws. The enabled fixture proves that the checker uses its supplied offsets pin.",
  '',
  'The patched tree pins are `35a4753f` (HOST24J base `189df6ac`) and `31c8f6b8` (N base `57a1f14d`). Both reproduce exactly with PATCH_PRIOR and zero fuzz.',
  '',
  'The production proof remains **MISSING**. No real prepared population was supplied. HOST_INPUTS.json names the missing final receipts, native pointing/pose/routing databases, launch VQA receipt, augmentation, and source seal by path or native field; no production PASS is claimed.',
  '',
  'The preparation receipt is `<proof root>/b/receipt.json`. Use `<root>/h/receipt.json` with the handover config, or `<root>/population/receipt.json` with entry.frame_host. HOST_INPUTS.json lists the fields checked for each.',
  '',
  'Before native preparation, bind `r1_training.direction_prior` to the packaged weights. Native `bind_prepared` emits `r2_sampling.direction_prior`; the checker requires both fields.',
  '',
  'Reproduce every reported test count and fixture statistic from this workspace:',
  '```bash',
  'export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1',
  'PY=/scratch/jjyeung/envs/p1cpu/bin/python',
  'nice -n 10 "$PY" scripts/test_checker.py',
  'nice -n 10 "$PY" scripts/test_offsets.py',
  'nice -n 10 "$PY" scripts/verify_trees.py',
  'nice -n 10 "$PY" scripts/test_host_wrapper.py',
  'nice -n 10 "$PY" scripts/test_integration.py',
  'nice -n 10 "$PY" scripts/finalize.py',
  '```',
  'The scripts use fresh output paths; retain existing evidence and select a fresh workspace for a rerun. Their source fixtures come from the supplied sibling prior2b and priorrev directories.',
  '',
  'Run this exact command on the training host after setting PY, PROOF_ROOT, BASE_TREE, PATCHED_TREE and a new CHECK_OUTPUT directory to their actual locations:',
  '```bash',host['training_host_command'],'```',
  'The wrapper derives all four stream receipts and offset tables from the selected preparation and saves the expanded command and input hashes in HOST_COMMAND.json. Use `--stage h` or `--stage population` with those configs. The checker reads N_LAUNCH_CONFIG.json and TOWARD_HARD_WEIGHTS.json from this package.',
  '',
  'The package is `out/fbp_prior2c.tar`; its digest is in `out/fbp_prior2c.tar.sha256`. `scripts/finalize.py` creates the archive, hashes every member, and verifies it against PACKAGE.json. ARCHIVE_CHECK.json records that result.',
 ]
 assert len(report)<=50
 (W/'out/REPORT.md').write_text('\n'.join(report)+'\n')
 (W/'STATUS.md').write_text(f"The production checker fixes both MUST items and the receipt-path documentation. All {summary['tests']} regression checks pass, including every prior2b checker test, both schedule tampers, the unlabelled fixture refusal, and unchanged labelled-fixture plans. The final report, host-input contract, tests, checker and archive are complete; the real production proof remains MISSING because the training-host preparation and native stores were not supplied.\n")
 # Include reviewable evidence and test fixtures, without duplicating reconstructed source trees.
 selected=[]
 for base in (W/'out',W/'scripts',W/'work'):
  for directory,dirs,names in os.walk(base):
   dirs[:]=sorted(n for n in dirs if n not in ('tree_verification','__pycache__','fixture_unchanged','package_candidates'))
   for name in sorted(names):
    p=Path(directory)/name
    if p.name in ('fbp_prior2c.tar','fbp_prior2c.tar.sha256','PACKAGE.json','ARCHIVE_CHECK.json',
                  'fixture_unchanged.log','finalize.log'):continue
    if p.parent==W/'work' and p.name.endswith('_inventory.json'):continue
    if p.suffix=='.pyc':continue
    selected.append(p)
 selected.append(W/'STATUS.md');selected=sorted(set(selected))
 members={str(p.relative_to(W)):pin(p)['sha256'] for p in selected}
 total=sum(p.stat().st_size for p in selected)
 if total>=20*1024**3:raise ValueError('WORKSPACE_PACKAGE_EXCEEDS_20_GIB')
 put(W/'out/PACKAGE.json',dict(status='PASS',files=members,files_count=len(members),payload_bytes=total,
                             command=PREFIX+' scripts/finalize.py'))
 selected.append(W/'out/PACKAGE.json')
 archive=W/'out/fbp_prior2c.tar'
 with tarfile.open(archive,'x') as tar:
  for p in selected:tar.add(p,arcname=str(p.relative_to(W)),recursive=False)
 archive_pin=pin(archive)
 (W/'out/fbp_prior2c.tar.sha256').write_text(archive_pin['sha256']+'  fbp_prior2c.tar\n')
 expected=dict(members,**{'out/PACKAGE.json':pin(W/'out/PACKAGE.json')['sha256']})
 actual={}
 with tarfile.open(archive,'r') as tar:
  for entry in tar:
   if not entry.isfile() or entry.name in actual:raise ValueError('UNEXPECTED_ARCHIVE_MEMBER:'+entry.name)
   h=hashlib.sha256()
   with tar.extractfile(entry) as f:
    for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
   actual[entry.name]=h.hexdigest()
 assert actual==expected,'ARCHIVE_MEMBER_MISMATCH'
 put(W/'out/ARCHIVE_CHECK.json',dict(status='PASS',archive=archive_pin,members=len(actual),bytes=archive.stat().st_size,
                                    command=PREFIX+' scripts/finalize.py'))
 print(json.dumps(dict(tests=summary['tests'],status=summary['status'],production_gate='MISSING',archive=archive_pin,
                       archive_members=len(actual),archive_bytes=archive.stat().st_size),indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--host-inputs',action='store_true');a=p.parse_args()
 if a.host_inputs:host_inputs()
 else:finalize()
