"""Deliver current CPU evidence and an independently verified local archive."""
from common import *
import ast,tarfile

CURRENT=['NAMED_INPUTS.json','K1_TRAIN_RESULTS.json','K1_TRAIN_DIAGNOSTICS.json','DOUBT_REMEASURE.json','SIZE_TODAY_DIAGNOSTIC.json','SELECTED_SIZE_SCREEN.json','CONSTRUCTION_SELECTION.json','GPU_NEED.json','TESTS0749.json','TRAIN_CENSUS.json','TRACK_SELECTION.json','CPU_TRACK_PLAN.json','K1_TRAIN_TABLES.md','REPORT.md','OBJECT_GATHER_READINESS.json','VALIDATION0749.json','bind0749.log','train0749.log','test0749.log']

def main():
 pins()
 for p in (ROOT/'inputs/ruling0749').glob('*.md'):sha(p)
 source=Path('/scratch/jjyeung/orch_n30/sb_kbox4/out/box_ladder/DECISION.json')
 raw=read(source);decision=json.loads(raw);q=ROOT/'inputs/kbox4/DECISION.json';q.write_bytes(raw)
 assert decision['freeze']['frozen_variant'] is None and decision['bars']['replace_box']['verdict']=='FAIL'
 cfg=js(ROOT/'config/KBOX_RULES_HOOK.json')
 write(ROOT/'out/OBJECT_GATHER_READINESS.json',dict(status='PARTIAL_TRAIN_SNAPSHOT',selection_split='K1-train',native_live_exports='MISSING',missing_exports=cfg['missing_native_exports'],expected_module=cfg['native_expected_module'],adapter=cfg['module_path'],adapter_scope='Pinned serialized training rows, object counts and replay receipt; price_k1_tracks refuses until native implementation and CUDA tracks exist',final_decision_path=str(q),final_decision_sha256=sha(q),verdicts={k:v['verdict'] for k,v in decision['bars'].items()},object_selected=False))
 bars={k:dict(type_points=v,ci95_lower_gt=0) for k,v in __import__('registration').CATEGORIES.items()}
 write(ROOT/'config/BARS.json',dict(version=2,ruling='20261119T0749Z',selection_split='K1-train',bars=bars,gates={'object_size_estimation':['replace_box_both_parts','selected_P0_P1_P2_size_screen_under_serving_and_g3t_s4','size_screen','treatment_ci95_lower_gt_minus_2'],'object_rel_distance':['replace_box_both_parts'],'obj_appearance_order':['first_seen_pair_rate_ge_0.90']},absolute_distance=dict(external_reader_comparison_only=True,present_path='cont_ops18 package D',binding=str(ROOT/'inputs/PACKAGE_D_BINDING.json'),S4_reconstruction=False),missing_rebuilt_table='Retain A0 own score in both paired arms',bootstrap=dict(draws=10000,seed=20261119,unit='physical room',estimate='item weighted')))
 result=js(ROOT/'out/K1_TRAIN_RESULTS.json');doubt=js(ROOT/'out/DOUBT_REMEASURE.json');tests=js(ROOT/'out/TESTS0749.json');diag=js(ROOT/'out/K1_TRAIN_DIAGNOSTICS.json');size=js(ROOT/'out/SIZE_TODAY_DIAGNOSTIC.json');binding=js(ROOT/'inputs/KBOX_SNAPSHOT.json')
 assert tests['status']=='PASS' and len(result['comparisons'])==272 and len(doubt['variants'])==33
 assert result['retained_A0_rows']==0
 for entry in binding['captures'].values():assert sha(ROOT/entry['snapshot_path'])==entry['snapshot_sha256']
 assert sha(cfg['module_path'])==cfg['module_sha256'] and sha(cfg['receipt_path'])==cfg['receipt_sha256']
 for p in (ROOT/'code').glob('*.py'):ast.parse(read(p),filename=str(p))
 assert not list((ROOT/'out/object_route').glob('LOOK_*.json'))
 for name in CURRENT:
  p=ROOT/'out'/name
  if p.exists() and p.suffix=='.json':assert 'input_sha256' in js(p),name
 d=doubt['variants']['A4_obj_0.25_best1'];gain=d['repair_gain'];rate=d['closer_rate'];first=diag['arms']['A0_deployed']['first_seen']
 report=[
 'The CPU deliverables are complete for the available K1 training measurements; live hook binding and selected-arm pricing remain blocked.',
 'The accepted specification matches SHA256 640e8deb8fe7d661abbeb3bb0d345aeb2b6eda4f50af346f0f16b0cf4788cce3.',
 'The named specification, 0749Z ruling and pilot record were each copied once from NFS; NAMED_INPUTS.json records their hashes.',
 '',
 'The pinned workload has 1,037 rows on 209 captures and 192 physical rooms. Its legacy table-covered subset has 883 rows.',
 'All 209 captures now have rebuilt label tables. The retain-A0 rule affects 0 rows; its nonzero-score behavior is regression-tested.',
 'A0 uses sb_kbox4 serving geometry: own-depth scale and own gravity. No S4 reconstruction serves as the present path.',
 'The CPU pass re-scores 33 merged variants and S4-today on both fixed rowsets, pooled and by dataset: 272 paired contrasts.',
 'K1_TRAIN_TABLES.md contains the tables; K1_TRAIN_RESULTS.json contains full dataset contrasts and input hashes.',
 'Command for workload binding and table availability: `bash scripts/train_cpu.sh code/bind0749.py`.',
 'Command for every score, count and interval below: `bash scripts/train_cpu.sh code/train0749.py`.',
 '',
 'The distance detector is the pilot’s explicit rule: the rarer object is grounded in fewer than 3 frames. It never uses truth to fire.',
 f"It fires on {d['triggered']} rows; {d['paired_numeric']} have two numeric values. Both measurements refuse on {d['first_refusals']} rows.",
 f"Diagnostic 0.25/best1 re-measurement is closer on {d['closer']}, worse on {d['worse']}, and tied on {d['ties']} paired rows.",
 f"Its closer rate is {100*rate['estimate']:.2f}% [95% CI {100*rate['ci95'][0]:.2f}, {100*rate['ci95'][1]:.2f}].",
 f"Switching only flagged rows changes full-row MRA by {gain['estimate']:+.3f} points [{gain['ci95'][0]:+.3f}, {gain['ci95'][1]:+.3f}].",
 'All 33 diagnostics, paired row evidence, closer-minus-worse intervals and refusal counts appear in DOUBT_REMEASURE.json.',
 'These diagnostics do not select a repair arm. No merged variant meets the box kit’s eligibility rule; no rows were built.',
 'The fitted three-field detector coefficients and threshold, and a size-specific trigger, are MISSING from the named pilot record.',
 '',
 f"A0 first-seen order is correct on {first['correct']}/{first['pairs']} operand pairs ({100*first['rate']['estimate']:.2f}%).",
 'K1_TRAIN_DIAGNOSTICS.json gives each merged variant’s first-seen rate, merge precision and capture/name object counts.',
 f"Today-only size diagnostics use {size['geometries']['serving']['objects']} deduplicated objects: serving MRA {size['geometries']['serving']['score']:.3f}, S4 MRA {size['geometries']['g3t_s4']['score']:.3f}.",
 f"The paired size change is {size['treatment']['estimate']:+.3f} [{size['treatment']['ci95'][0]:+.3f}, {size['treatment']['ci95'][1]:+.3f}] points, with refusals scored zero.",
 'That diagnostic cannot satisfy the selected-construction screen. P0 is refused; P1 evidence is MISSING; P2 requires CUDA.',
 'The size gate requires the selected P0/P1/P2 construction on the same object set under both geometries before any size look.',
 '',
 'The final sb_kbox4 DECISION.json is bound: replace_box, size_screen and first_seen_screen all FAIL; frozen_variant is null.',
 'The hook binds serialized object_source, count_objects and stage1_replay through code/kbox_snapshot.py.',
 'Native count_objects, object_source, price_k1_tracks and stage1_replay exports are MISSING from sb_kbox4’s top-level modules.',
 'Expected native module: /scratch/jjyeung/orch_n30/sb_kbox4/box_math.py. The tracking-price adapter refuses explicitly.',
 'Expected P1 input: inputs/TOWER_DECISION.json. Expected P2 output: out/object_route/K1_TRACK.json.',
 'The package-D binding has MISSING step-544/job-172957 and step-200 slots, each for 290 twins plus 290 reworded items.',
 'Expected returns: /scratch/jjyeung/orch_n30/cont_ops*/; bounded `ls -d` found no directory. No return filename was invented.',
 'The absolute-distance comparison refuses without pinned package-D path/SHA256 records; its S4 reconstruction branch is removed.',
 '',
 'GPU_NEED.json retains K1 tracking only: 1.3 hours estimated, 1.75-hour cumulative hard stop, one 48-GiB card; none used.',
 'scripts/gpu_k1_track.sh uses vnice, /scratch caches, a local lock and separately required authorization/ledger receipts.',
 'No CUDA predictor was attempted. The retained first GPU minute checks the staged predictor before the full pass.',
 f"Validation: {tests['tests']} regression checks pass; `bash scripts/train_cpu.sh code/test0749.py`; `bash -n scripts/train_cpu.sh scripts/gpu_k1_track.sh`.",
 'The checks cover retained nonzero A0 scores, pairing, truth-independent triggers, refused repairs, construction order and missing-input gates.',
 'No R0-dev, K1 held-out, GPU, network, SSH, Git, process termination or tmux operation ran. All writes stayed in this workspace.',
 'Archive and member verification: `bash scripts/train_cpu.sh code/final0749.py`; `sha256sum -c out/sb_kobj4.tar.sha256`.',
 'Deliverables: out/REPORT.md, out/K1_TRAIN_TABLES.md, out/GPU_NEED.json, out/sb_kobj4.tar and its SHA256 sidecar.',
 'No borderline revision-history prose is retained.',
 ]
 assert len(report)<=60
 (ROOT/'out/REPORT.md').write_text('\n'.join(report)+'\n')
 write(ROOT/'out/VALIDATION0749.json',dict(status='PASS',checks=dict(regression_tests=tests['tests'],snapshot_captures=len(binding['captures']),paired_contrasts=len(result['comparisons']),doubt_variants=len(doubt['variants']),production_evaluation_reads=0,report_lines=len(report)),command='bash scripts/train_cpu.sh code/final0749.py'))
 status('Stage 4: Available CPU work and 13 regression checks are complete. All 33 merged variants are priced on K1 training; the retained-A0 count is zero. Selected-arm evaluation remains blocked by failed box eligibility, missing P1 evidence, CUDA tracking and native live hook exports. Package-D remains MISSING. Report, tables, GPU plan and a member-verified archive with SHA256 are delivered; no evaluation split was read.')
 # Archive only current deliverables, not copied historical reports or nested archives.
 members=[p for folder in ['code','config','inputs'] for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 members += [ROOT/'scripts'/n for n in ['train_cpu.sh','gpu_k1_track.sh']]+[ROOT/'STATUS.md']+[ROOT/'out'/n for n in CURRENT]
 for p in members:assert p.exists(),p
 hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(members))}
 write(ROOT/'out/ARCHIVE_MANIFEST.json',dict(status='COMPLETE',members=hashes))
 manifest=ROOT/'out/ARCHIVE_MANIFEST.json';hashes[str(manifest.relative_to(ROOT))]=sha(manifest)
 archive=ROOT/'out/sb_kobj4.tar'
 with tarfile.open(archive,'w') as tf:
  for name in sorted(hashes):tf.add(ROOT/name,arcname=name,recursive=False)
 with tarfile.open(archive,'r') as tf:
  assert set(tf.getnames())==set(hashes)
  for name,h in hashes.items():assert hashlib.sha256(tf.extractfile(name).read()).hexdigest()==h,name
 h=sha(archive);(ROOT/'out/sb_kobj4.tar.sha256').write_text(h+'  out/sb_kobj4.tar\n')
 write(ROOT/'out/PACKAGE.json',dict(status='COMPLETE',evaluation_status='AVAILABLE_CPU_COMPLETE_SELECTED_ARM_BLOCKED',archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(hashes),verified=True))
 print(json.dumps(dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(hashes),report_lines=len(report))))

if __name__=='__main__':main()
