"""Publish measured results, exact missing inputs, reproducible commands and an archive."""
import json,hashlib,sys,tarfile,os
from pathlib import Path
W=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def pin(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def load(p):return json.loads(Path(p).read_text())
inputs=[pin(__file__)]
def read(name):
 p=W/name;inputs.append(pin(p));return load(p)
def put(name,v):
 p=W/name;p.write_text(json.dumps(dict(v,inputs=inputs.copy()),sort_keys=True,indent=2)+'\n');return pin(p)
source=read('out/SOURCE_RECONSTRUCTION.json');audit=read('out/INPUT_AUDIT_FINAL.json');stores=read('out/STORE_AUDIT.json');count=read('out/COUNT_CROSSCHECK.json')
seal=read('out/SEALED_PATCH.json');live=read('out/LIVE_PATCH.json');gate=read('work/final_gate/RESULT.json');negative=read('out/CHECKER_NEGATIVE_TESTS.json')
new=read('out/INTEGRATION_sealed_new.json');base=read('out/INTEGRATION_sealed_base.json');livetest=read('out/INTEGRATION_live_new.json')
inputs.extend([pin(W/'out/prove_on_prepared.py'),pin(W/'out/PATCH_PRIOR.patch'),pin(W/'out/TOWARD_HARD_WEIGHTS.json')])
assert gate['status']=='PASS',gate.get('error');assert negative['status']=='PASS';assert seal['status']=='PASS';assert livetest['status']=='PASS'
# Retain all existing failures and compare by exact test identity and error.
base_records={v['id']:v for v in base['records']};new_records={v['id']:v for v in new['records']}
worsened=[v for k,v in new_records.items() if k in base_records and v['status']!='PASS' and v!=base_records[k]]
added=[v for k,v in new_records.items() if k not in base_records]
assert not worsened and len(added)==9 and all(v['status']=='PASS' for v in added)
commands={
 'live_tree':'scripts/setup_live.py', 'sealed_tree':'scripts/sealed_tree.py',
 'input_recovery':'scripts/recover_metadata.py', 'pin_audit':'scripts/inspect_pins.py', 'final_pin_audit':'scripts/supplement_inputs.py',
 'source_counts':'scripts/source_census.py', 'count_crosscheck':'scripts/build_fixture.py', 'store_hashes':'scripts/store_audit.py',
 'native_fixture':'scripts/native_fixture.py', 'pose_order_fixture':'scripts/mix_fixture.py',
 'identity_gate':'out/prove_on_prepared.py --base-tree work/sealed_base --patched-tree work/sealed_new --weights out/TOWARD_HARD_WEIGHTS.json --fixture work/mix_fixture/FIXTURE.json --output-dir work/final_gate',
 'negative_checker_tests':'scripts/test_checker.py',
 'sealed_base_tests':'scripts/test_live.py sealed_base', 'sealed_patched_tests':'scripts/test_live.py sealed_new',
 'live_patch_tests':'scripts/test_live.py live_new tests.test_r1_direction_prior', 'report_and_archive':'scripts/finalize.py'}
prefix='OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python '
commands={k:prefix+v for k,v in commands.items()}
missing=[]
for stream,item in stores['streams'].items():
 for v in item.get('missing',[]):missing.append(dict(cell={'routing':'routing_base'}.get(stream,stream),kind='native_source_input',**v))
prep='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json'
missing.append(dict(cell='ALL',kind='final_preparation',path=prep,sha256='MISSING',status='MISSING'))
for v in audit['pins']:
 if v['status']=='MISSING':missing.append(dict(cell='launch_pin',kind='pinned_launch_input',**v))
card=load(W/'work/fixture/card.json');inputcard=pin(W/'work/fixture/card.json');inputs.append(inputcard)
cells={c['type']:dict(stream=c['stream'],production_status='MISSING',field_absent_production_identity='MISSING',field_present_production_identity='MISSING',source_metadata_rows=source['cells'].get(c['type'],'MISSING'),fixture=gate['cells'][c['type']]) for c in card['cells']}
summary={}
for mode in ('base','enabled'):
 summary[mode]={}
 for cell,a in gate['loader_audits'][mode].items():
  summary[mode][cell]=next(v for v in a['answer_shares'] if (v['clause'],v['difficulty'])==('toward','hard'))
allpins=[v for v in audit['pins'] if v['status']!='PASS']
proof=dict(verdict='NO_GO',production_all_cell_gate='MISSING',real_prepared_gate='MISSING',
 reason='Native pointing/routing stores, pose source stores, and final prepared offset tables are unavailable. Launch population/indices are incomplete zero-count placeholders. Source-filter and fixture identities cannot replace production evidence.',
 cells=cells,source_filter_scope=source['scope'],source_counts=source['source_counts'],source_eligible=source['eligible_vqa'],source_stages=source['stages'],
 launch_kit_content_comparison='PASS' if not audit['launch_kit_differing_fields_ignoring_paths'] else 'MISMATCH',
 count_crosscheck=count['cells'],store_crosscheck=stores['streams'],unverified_or_mismatched_launch_pins=allpins,
 seal_patch=seal,supplied_live_tree_mismatches=live['mismatches'],missing=missing,
 fixture=dict(status=gate['status'],scope=gate['scope'],production_gate=gate['production_gate'],seed=gate['seed'],steps=gate['steps'],
              cells_tested=len(gate['cells']),total_draws=sum(c['draws'] for c in gate['cells'].values()),global_checks=gate['global_checks'],
              max_repeats=gate['max_repeats'],toward_hard=summary,loader_audits=gate['loader_audits'],plan_sha256=gate['plan_sha256'],evidence=pin(W/'work/final_gate/RESULT.json')),
 commands=commands)
proofpin=put('out/PROOF.json',proof);inputs.append(proofpin)
tests=dict(status='NO_NEW_FAILURE_WITH_EXISTING_MISSING_FIXTURES',all_tests_pass=False,
 sealed_base={k:base[k] for k in ('tests','errors','failures','skips')},sealed_patched={k:new[k] for k in ('tests','errors','failures','skips')},
 added_tests=added,worsened_existing_tests=worsened,existing_missing_fixture_errors=[v for v in new['records'] if v['status']!='PASS'],
 live_tree_prior_tests={k:livetest[k] for k in ('status','tests','errors','failures','skips')},native_receipt_fixture=dict(status=gate['status'],cells=len(gate['cells']),scope=gate['scope']),
 fail_closed_checker=negative,patch_application=seal,commands={k:v for k,v in commands.items() if 'test' in k or 'gate' in k})
testpin=put('out/TESTS.json',tests);inputs.append(testpin)
host=dict(status='MISSING_REAL_PREPARATION',preparation=dict(path=prep,expected_name='receipt.json',sha256='MISSING',required_fields=['streams','r2_sampling','r1_training']),
 config=dict(path='MISSING: use the final config emitted by r1_population.bind_prepared',expected_name='config.json',required_fields=['preparation','r2_sampling','r1_training.row_plan_sha256']),
 stream_receipts={s:dict(launch_receipt=stores['streams'][s]['receipt'],required_final_path_field='receipt.streams.'+s+'.receipt.path',note='Use the receipt pinned by the final preparation; it may be a rebuilt receipt.') for s in ('pointing','pose','routing','vqa')},
 post_filter_tables={s:dict(path='MISSING until final receipt exists',expected_name=s+('_order.json' if s=='pose' else '_indices.json'),required_field='receipt.streams.'+s+('.order' if s=='pose' else '.indices')) for s in ('pointing','pose','routing','vqa')},
 population=dict(path='MISSING until final receipt exists',expected_name='population.json',required_field='receipt.r2_sampling.population'),
 indices=dict(path='MISSING until final receipt exists',expected_name='indices.json',required_field='receipt.r2_sampling.indices'),
 transitive_inputs='Every receipt/database/indices/order/membership pin opened by native Rows, plus the card and prior weights. --pin SHA256=PATH relocates exact bytes.',
 source_stores_missing=missing[:5],base_tree='work/sealed_base',patched_tree='work/sealed_new',weights='out/TOWARD_HARD_WEIGHTS.json')
hostpin=put('out/HOST_INPUTS.json',host);inputs.append(hostpin)
# Preserve the exact resolver version used to authenticate capsule recovery.
snapshot=W/'work/code_snapshots/35fa97a17ef2d8f6ad2373101bc09dff29c2ff22abe3d20b85456142af796aa6'
put('out/CODE_SNAPSHOTS.json',dict(snapshots=[dict(original_path=str(W/'scripts/common.py'),**pin(snapshot))]))
lines=[
'**NO_GO.** The all-cell production identity proof is MISSING for `pointing`, `pose`, and `routing_base`; their native data and final post-filter offsets are unavailable. No real prepared receipt was synthesized.',
'',
'`PROOF.json` records every cell, filter-stage count/hash, mismatch and missing path. `TESTS.json` records the tests; `HOST_INPUTS.json` names the training-host fields and files.',
'',
'The 12 launch removal lists, naming removal, s/u/u_union, aliases, bindings, wordings and room-authority bytes authenticate. The metadata-filter replay retains **189,063 VQA rows** from 204,413 source rows plus 7,971 twins. All 18 VQA cell counts match their explicit card ceilings, including 55,808 direction and 42,507 facing-pair rows.',
'Frame-host rebuild/admission and final native offsets remain unproved. The launch population has `complete=false`, `after_all_filters=false`, 31 zero counts and 31 empty index lists; its 16 nonzero VQA source-count comparisons are MISMATCH, recorded without substitution.',
'',
'Launch `0e78d7f8` and kit `2ad4032d` agree in counts and pins after ignoring paths. Pointing `c09bb5ca`, routing `4e8e6c04`, and composite pose `6d591440` receipt identities match; only VQA store bytes `210b2534` are locally verified.',
'The mirrored VQA receipt hashes to `8091154c`, versus launch pin `e3ee51da` (MISMATCH). The copied admission review hashes to `30cf2da5`, versus `c3cfe01f` (MISMATCH). `INPUT_AUDIT_FINAL.json` gives full hashes and all unresolved pins.',
'',
'The exact 940-file seal `189df6ac` is reproducible from the authenticated base plus HOST24J.patch. PATCH_PRIOR applies with `--fuzz=0`, without offsets. The supplied live tree itself differs from that seal in `launch_r1/entry.py` and `launch_r1/production_proof.py`; `LIVE_PATCH.json` records both mismatches.',
'',
'**Fixture results only:** the same gate runs through native `Rows`, pose mix/order tables and reader-filter subset validation. Its 31 cells and 288,000 seed-17 draws pass: field absent equals base byte-for-byte; field present changes only toward-hard slots in direction/facing_pairs; all other positions and counts match. Each row appears at most four times; resume matches.',
'',
'| Cell / toward-hard | Draws | Base back | Patched back |',
'|---|---:|---:|---:|']
for cell in ('direction','facing_pairs'):
 b=summary['base'][cell];a=summary['enabled'][cell]
 lines.append(f"| {cell} | {a['draws']:,} | {b['back']['draws']:,} ({100*b['back']['share']:.4f}%) | {a['back']['draws']:,} ({100*a['back']['share']:.4f}%) |")
lines.extend([
'',
'Each other clause × difficulty group is unchanged. The fixture uses reconstructed VQA source rows and explicitly synthetic support rows for the three unavailable streams. It grants no production PASS.',
'',
'All nine added prior tests pass on both the reconstructed seal and the supplied live tree. The broader patched suite has 40 tests: 37 pass, zero fail, and three error; the base has the same three errors. They require missing `fixtures/work/build6/INIT_INPUT.json`. No existing result worsens. All five checker refusal tests pass.',
'',
'Commands below produce the reported counts, hashes, draw shares and test totals from this workspace. They retain fixtures; use a fresh workspace/output directory when repeating them.',
'```bash',
'export OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1',
'PY=/scratch/jjyeung/envs/p1cpu/bin/python',
'nice -n 10 "$PY" scripts/setup_live.py',
'nice -n 10 "$PY" scripts/sealed_tree.py',
'nice -n 10 "$PY" scripts/recover_metadata.py',
'nice -n 10 "$PY" scripts/inspect_pins.py',
'nice -n 10 "$PY" scripts/supplement_inputs.py',
'nice -n 10 "$PY" scripts/source_census.py',
'nice -n 10 "$PY" scripts/store_audit.py',
'nice -n 10 "$PY" scripts/build_fixture.py',
'nice -n 10 "$PY" scripts/native_fixture.py',
'nice -n 10 "$PY" scripts/mix_fixture.py',
'nice -n 10 "$PY" out/prove_on_prepared.py --base-tree work/sealed_base --patched-tree work/sealed_new --weights out/TOWARD_HARD_WEIGHTS.json --fixture work/mix_fixture/FIXTURE.json --output-dir work/final_gate',
'ln -s /scratch/jjyeung/orch_n30/fb_pack/prior2/work/base work/tree_r1_base',
'nice -n 10 "$PY" scripts/test_live.py sealed_base',
'nice -n 10 "$PY" scripts/test_live.py sealed_new',
'nice -n 10 "$PY" scripts/test_live.py live_new tests.test_r1_direction_prior',
'nice -n 10 "$PY" scripts/test_checker.py',
'nice -n 10 "$PY" scripts/finalize.py',
'```',
'',
'Training-host command (variables must name real files identified by `HOST_INPUTS.json`; no guessed table paths):',
'```bash',
'nice -n 10 "$PY" out/prove_on_prepared.py --base-tree work/sealed_base --patched-tree work/sealed_new --weights out/TOWARD_HARD_WEIGHTS.json \\',
'  --config "$N_CONFIG" --prepared-receipt "$N_PREP" --output-dir "$NEW_PROOF_DIR" \\',
'  --receipt pointing="$POINT_RECEIPT" --receipt pose="$POSE_RECEIPT" --receipt routing="$ROUTE_RECEIPT" --receipt vqa="$VQA_RECEIPT" \\',
'  --offset-table pointing="$POINT_INDICES" --offset-table pose="$POSE_ORDER" --offset-table routing="$ROUTE_INDICES" --offset-table vqa="$VQA_INDICES"',
'```',
'',
'`N_PREP` is `/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json` (MISSING). Exact final table paths/hashes must come from its stream pins. The checker prints PASS/FAIL for each cell and refuses incomplete populations, changed hashes, duplicate offsets and fixtures passed as real preparation.',
'',
'`fbp_prior2b.tar.sha256` authenticates the archive. `PACKAGE.json` records member hashes; native JSON arrays and unchanged input copies inherit provenance through their pinned fixture manifests.'
])
assert len(lines)<=80,len(lines)
(W/'out/REPORT.md').write_text('\n'.join(lines)+'\n')
(W/'STATUS.md').write_text('NO_GO: production pointing, pose and routing populations and final prepared offset tables remain MISSING. All supplied VQA metadata filters and 18 card ceilings check; the native-reader fixture passes 31 cells and 288,000 draws, and all nine PATCH_PRIOR tests pass. The exact 189df6ac seal accepts the patch without fuzz, while the supplied live tree and two receipt pins have explicitly reported mismatches. REPORT.md, PROOF.json, TESTS.json and the tested prepared-receipt checker are complete.\n')
# Package the final evidence and reproducible native-reader fixture, excluding exploratory runs.
files=[W/'STATUS.md']
for p in sorted((W/'out').glob('*')):
 if p.is_file() and p.name not in ('fbp_prior2b.tar','fbp_prior2b.tar.sha256','PACKAGE.json','finalize.log','ARCHIVE_CHECK.json') and not p.name.startswith(('TEST_','fixture_gate','native_gate','mix_gate','integration.log')):files.append(p)
files.extend(sorted((W/'scripts').glob('*.py')))
for directory in ('work/sealed_base','work/sealed_new','work/source','work/fixture','work/native_fixture','work/mix_fixture','work/final_gate','work/code_snapshots','work/recovered'):
 for p in sorted((W/directory).rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and not p.is_symlink():files.append(p)
files.append(W/'work/local_store_paths.txt')
files=sorted(set(files));members={str(p.relative_to(W)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files}
package=dict(schema='fbp-prior2b-package-v1',members=members,total_member_bytes=sum(v['bytes'] for v in members.values()),inputs=[pin(W/'out/REPORT.md'),pin(W/'out/PROOF.json'),pin(W/'out/TESTS.json'),pin(__file__)])
(W/'out/PACKAGE.json').write_text(json.dumps(package,indent=2,sort_keys=True)+'\n');files.append(W/'out/PACKAGE.json')
archive=W/'out/fbp_prior2b.tar'
with tarfile.open(archive,'w') as tar:
 for p in files:tar.add(p,arcname=str(p.relative_to(W)),recursive=False)
h=sha(archive);(W/'out/fbp_prior2b.tar.sha256').write_text(h+'  fbp_prior2b.tar\n')
print(json.dumps(dict(verdict='NO_GO',report_lines=len(lines),archive=str(archive),bytes=archive.stat().st_size,sha256=h,fixture_cells=len(gate['cells']),added_tests=len(added)),indent=2))
