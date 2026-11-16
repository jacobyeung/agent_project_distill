from pathlib import Path
import json,hashlib,re
import os
RUN_PREFIX=os.environ.get('REPIN_RUN_PREFIX','fix1')
TEST_RUN=os.environ.get('REPIN_TEST_RUN','test_fix1')
R=Path.cwd();O=R/'out'
tests=int(re.search(r'(\d+) passed', (O/'tests.log').read_text())[1])
offkit_tests=int(re.search(r'(\d+) passed', (O/'offkit_tests.log').read_text())[1])
archives=json.loads((O/'PACKAGE_PINS.json').read_text())
summary={}
for p in (R/'work'/TEST_RUN).glob('test_accepted_report_*/packet/reports/B2048.json'):
 r=json.loads(p.read_text());summary[r['benchmark']]=dict(items=r['items'],scenes=r['scenes'],score=r['headline']['score'],percentile_95=r['headline']['percentile_95'],first_line=r['first_line'],float_order_check=r['float_order_check'])
assert len(summary)==2
rehearsals={}
step544_rehearsals={}
for key in ('vsi','revsi'):
 r=json.loads((R/'work'/(RUN_PREFIX+'_'+key+'_done')/'RESULT.json').read_text())
 assert r['passed'] and r['config_mode']=='production' and r['reports'] and r['fetch']
 proof=json.loads((Path(r['config']['spec']['run'])/'metadata/P9.json').read_text())
 stage=json.loads((Path(r['job_root'])/'exports/359fcc3c_m200/RECEIPT.json').read_text())
 assert proof['passed'] and stage['status']=='complete' and stage['checker']['status']=='VERIFIED'
 rehear=dict(passed=True,fixture_decoded_items=r['items'],production_membership=r['production_membership'],
             prompt_proof=proof,full_checker_status=stage['checker']['status'],return_bytes=r['archive_bytes'],
             fetch=r['fetch'],reports=r['reports'],fixture_only=True)
 rehearsals[key]=rehear
 fixture=json.loads((R/'work'/(RUN_PREFIX+'_'+key+'_step544')/'RESULT.json').read_text())
 assert fixture['passed'] and fixture['config_mode']=='production' and fixture['fetch'] and fixture['reports']
 for result in (r,fixture):
  for report in (Path(result['fixture_packet'])/'reports').glob('*.json'):
   labelled=json.loads(report.read_text())
   assert labelled['mode']=='production' and 'EXPORT fixture' in labelled['first_line']
   assert labelled['frames']['count']==32 and labelled['frames']['layout']=='duplicate'
 step544_rehearsals[key]=dict(passed=True,fixture_decoded_items=fixture['items'],fetch=fixture['fetch'],reports=fixture['reports'],fixture_only=True)
(O/'VALIDATION.json').write_text(json.dumps(dict(tests=tests,offkit_tests=offkit_tests,accepted=summary,rehearsals=rehearsals,step544_rehearsals=step544_rehearsals,offkit_pins=json.loads((O/'OFFKIT_PINS.json').read_text())),indent=1)+'\n')
lines=['# Re-bind readiness\n\nThe two packages are ready for operator preparation with the final init-selection record. Nothing was submitted. The builder did not choose a D0 export. The init-selection owner must supply the decision required by item 7; `prepare` checks the selected SHA and step, registered rule hash and D0-ended reference against the completion record.\n\n']
lines.append('## Packages\n\n| Archive | Bytes | SHA256 |\n|---|---:|---|\n')
for key,a in archives.items():lines.append(f"| [{a['path'].split('/')[-1]}]({a['path'].split('/')[-1]}) | {a['bytes']} | `{a['sha256']}` |\n")
lines.append('\nEach archive contains only regular tar members. The generated payload and bootstrap tars also contain only regular members. Extract both packages into the same Trinity directory to install both benchmark choices. Submit only the generated opaque stdin batch. Do not upload these archives or BINDING.json to Orchard.\n\n')
lines.append(f'## Validation\n\nAll {tests} Build R tests passed in `tests.log`; all {offkit_tests} offkit tests passed in `offkit_tests.log`. The tests compare exact floats against the accepted returns, verify payload and step544 staging bytes, check complete production item membership, reject invalid bindings, check submission accounting, and exercise four-part admission with the unchanged full checker. The governor-registration unit test uses process stand-ins and performs no live registration.\n\n| Read | Items | Scenes | B2048 mean | Scene-bootstrap 95% interval |\n|---|---:|---:|---:|---|\n')
for bench,r in summary.items():lines.append(f"| `{bench}` | {r['items']} | {r['scenes']} | {100*r['score']:.2f} | [{100*r['percentile_95'][0]:.1f}, {100*r['percentile_95'][1]:.1f}] |\n")
lines.append('\n`VALIDATION.json` records the exact values. B2048 is primary; ON16k and B4096 are secondary. All three budgets reproduce the accepted headline and group floats. The imported offkit aggregator can differ from the accepted scorer by floating-point accumulation order. The reporter first checks agreement within 1e-12, then retains the unchanged accepted scorer’s recomputed floats. It records every correction. It does not take values from a benchmark report file during production reporting. The six imported offkit files match `OFFKIT_PINS.json`; the launcher verifies their content before importing offkit and before every action. Each archive includes that manifest.\n\n')
lines.append('Both complete D0 CPU rehearsals passed staging, whole-tar authentication, the unchanged full export checker, the accepted prompt-byte proof with a template stand-in, fake-model decoding, processor comparisons, budget continuation, merge, pool publication, verified local fetch, and labelled report generation. VSI decoded 14 fixture items: two per non-direction group and four direction items so that all three direction subtypes appear. ReVSI decoded two fixture items per category, for ten total. Separate production-loader tests selected exactly 4,008 and 679 accepted IDs, with no absolute-distance or room-size item. The full cohorts were not decoded by a model in this build.\n\nThe rehearsal CONFIG retains production mode and the accepted budgets and decoding policy. Local model, media, path and transport stand-ins replace the remote assets. The task-provider boundary supplies the fixed accepted proof subset with constant synthetic answers, and a fixture membership assertion checks those IDs. Fixture reports say `EXPORT fixture`; their binding and worker CONFIG retain production mode to exercise the production path. These rehearsals test control flow, not model quality or real-processor equivalence.\n\n`rehearsal_vsi_done.log` and `rehearsal_revsi_done.log` record the final D0 passes. `rehearsal_vsi.log` and `rehearsal_revsi.log` record the step544-path fixture passes. `COVERAGE_vsi.json` and `COVERAGE_revsi.json` identify executed lines and source hashes, including child prompt-proof and checker processes. `ORCHARD_ONLY.md` and `COVERAGE_LIMITS.json` list unobserved runtime lines and explain the hardware and transport boundaries.\n\n')
lines.append('## Change scope\n\n[DIFF.md](../DIFF.md) gives one complete line-range table per benchmark. The patches `SOURCE_vsi.patch` and `SOURCE_revsi.patch` preserve every changed source line. PATH/ENV changes cover the opaque return aliases and Trinity package prefixes. BEYOND changes cover the bootstrap binding/parity guard, D0 stage dispatcher, unchanged readk stager addition, retained pool write-test file, tracing entry, governed fetch callback, Trinity launcher, reports and tests. The accepted reader, scorer, items, media manifest, processor code, frame plan and step544 stager retain their bytes.\n\nThe new return pool is `/project/community/jjyeung/okh7/9e6b70a213c84fd0/`; GCS uses `gs://cmu-gpucloud-jjyeung/q8/9e6b70a213c84fd0/<token>/`. Job names use `a15_cot_ap` plus hexadecimal tokens. `ORCHARD_NAMES.md` lists inherited benchmark, dataset, model and project strings; `INHERITED_NAMES.json` identifies their source files. New binding/export identifiers use opaque fields `x0` and `x1`. Token meanings are recorded only in `work/ORCHARD_LEDGER.jsonl`. Production submission records alone append the official-read ledger.\n\n')
lines.append('## Operation and limits\n\n[RUN.md](../RUN.md) gives exact preparation, submission, polling, governed fetch and report commands for both benchmarks. VSI takes the accepted 35-minute reference plus D0 staging; ReVSI takes 13 minutes plus staging. Allow roughly 9–27 additional minutes for a 21.583 GB export under the stated transfer assumptions. Reserve 220 GB and 180 GB of additional job-local disk, respectively, while preserving the 200 GiB free-space floor. The build remains below its 2 GB limit; `FINAL_CHECK.json` records its measured size.\n\nNo SSH, network, Git, GPU, Slurm or Orchard command ran. Real Orchard runtime interiors, credentials, media, H100 execution, real-processor parity, live governor admission and remote return channels remain unverified. The runtime checks refuse before decoding if export authentication or prompt proof fails. No benchmark answer or score selected an export, item, budget or policy. No external source file was modified.\n\nThe documentation applies the no-archaeology skill. It retains no borderline project-history sentence; accepted package identities and diff baselines are required provenance.\n\n')
source=(R/'kit/rebind.py').read_text().splitlines()
def line_of(needle):return next(i for i,line in enumerate(source,1) if needle in line)
lines.append('## Review fixes\n\n')
lines.append(f"Fix 4: `kit/rebind.py:{line_of('m(200|400|600|800|1000)')}` admits only the five init-rule candidates. The reviewed `export_stage.parse_done` call remains at `kit/rebind.py:{line_of('rec = E.parse_done')}`. Tests refuse an m100 completion record with matching SHA, selected step, rule hash and D0-ended fields; a separate test checks the launcher guard independently of offkit.\n\n")
lines.append(f"Fix 6: `kit/rebind.py:{line_of('def verify_offkit_pins')}` verifies `bind.py`, `report.py`, `spec.py`, `adapt_direct.py`, `frames.py` and `__init__.py` against the shipped manifest before importing them. Every action repeats the check. Tests refuse mutations to each module on `sys.path`, prove that changed code does not execute, and refuse mutations after import for all five actions.\n\n")
lines.append(f"The verified-binding report API is used at `kit/rebind.py:{line_of('rep = reports.label_report')}`. Bindings hash the 32-duplicate frame layout. `RUN.md` specifies every required init-selection field and the production ledger.\n\n")
lines.append('## Shipped file hashes\n\n`SHIP_SHA256SUMS` contains the same complete inventory below. These hashes cover every file shipped inside either archive.\n\n```text\n'+(O/'SHIP_SHA256SUMS').read_text()+'```\n')
(O/'REBIND_READY.md').write_text(''.join(lines))
# Check shipped bytes and package contents once after all documentation is complete.
import tarfile
for a in archives.values():
 p=R/a['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
 with tarfile.open(p) as tf:
  for m in tf:
   assert m.isfile() and not m.islnk() and not m.issym()
   assert tf.extractfile(m).read()==(R/m.name).read_bytes(),m.name
for line in (O/'SHIP_SHA256SUMS').read_text().splitlines():
 digest,name=line.split('  ',1)
 assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
for name,digest in json.loads((O/'OFFKIT_PINS.json').read_text()).items():
 assert hashlib.sha256((Path('/scratch/jjyeung/orch_n30/b07_offread/kit/offkit')/name).read_bytes()).hexdigest()==digest,name
retained=Path(json.loads((R/'work/REPIN2_RUN.json').read_text())['previous'])
old=json.loads((retained/'PACKAGE_PINS.json').read_text())
for key, value in old.items():
 assert hashlib.sha256((retained/f'package_{key}.tar').read_bytes()).hexdigest()==value['sha256']
(O/'FINAL_CHECK.json').write_text(json.dumps(dict(package_members_match_workspace=True,regular_members_only=True,
    tests=tests,offkit_tests=offkit_tests,cpu_rehearsals=4,offkit_pins_verified=True,
    ship_inventory_verified=True,retained_archives=str(retained.relative_to(R)),retained_archive_hashes_verified=True,
    package_sha256={key:a['sha256'] for key,a in archives.items()},
    ready_sha256=hashlib.sha256((O/'REBIND_READY.md').read_bytes()).hexdigest(),workspace_bytes=sum(p.stat().st_size for p in R.rglob('*') if p.is_file() and not p.is_symlink())),indent=1)+'\n')
assert json.loads((O/'FINAL_CHECK.json').read_text())['workspace_bytes']<2_000_000_000
print('Ready report and final archive checks completed.')
