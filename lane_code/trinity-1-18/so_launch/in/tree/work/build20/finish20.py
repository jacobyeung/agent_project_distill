from pathlib import Path
import collections,datetime,json
L=Path(__file__).resolve().parents[2];B=L/'work/build20'
def read(p):return json.loads((L/p).read_text())
def write(p,v):(L/p).write_text(json.dumps(v,indent=2)+'\n')
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
write('work/build20/SUITE_RUNS.json',dict(r2=dict(status='INCOMPLETE',reason='Operator interrupted this build-owned suite before its outputs could exceed the workspace cap. No completed suite result is claimed.',exit_code=130,source='work/build20/proofs/final/suite_tree/r2/console.log'),generator=dict(status='NOT RUN',reason='Required external input absent',source='work/build20/proofs/final/suite_tree/generator/NOT_RERUN.json'),legacy=dict(status='NOT RUN',reason='Required external input absent',source='work/build20/proofs/final/suite_tree/legacy/NOT_RERUN.json')))
seal=read('out/TREE_SEAL.json')['tree_sha256'];up=read('work/build20/UPLOADS.json');op=read('work/build20/proofs/operator/RESULT.json');cov=read('work/build20/DELTA_COVERAGE.json');receipts=read('work/build20/proofs/receipts/RESULT.json')
packet=read('work/build20/proofs/final/packet/results.json');counts=collections.Counter(v['outcome'] for v in packet.values())
write('work/build20/VALIDATION.json',dict(timestamp=stamp,GO=False,tree_seal=seal,packet_outcomes=dict(counts),packet_failures={k:v for k,v in packet.items() if v['outcome']!='passed'},tests={n:read('work/build20/proofs/'+n+'/TESTS.json') for n in ('before','review','retained19','final_focused','edges','producer_edges','edge20','job')},tree_mutations=read('work/build20/proofs/mutations/RESULT.json'),job_mutations=read('work/build20/proofs/job_mutations/RESULT.json'),coverage=dict(tree_observed=cov['observed'],tree_total=cov['total'],job_observed=cov['job_library']['observed'],job_total=cov['job_library']['total'])))
operator='''This kit is unsubmitted and GO=false. The capacity fixture and full frozen suite did not complete. The local shell test captures bwrap arguments after staging; it does not qualify a real allocation. Review the build report before using these commands.

Run these commands on the Orchard login host from the extracted delivery root. They write only to N's own pool folder. P's kit and run remain read-only.

```bash
python3 -I -s -B work/build20/upload.py "$PWD" /project/community/jjyeung/okh7/x_90a20c41
mkdir -p /project/community/jjyeung/okh7/x_90a20c41/o
```

After P's export lands, supply `/project/community/jjyeung/okh7/x_90a20c41/g.json`. This is the normalized, offline listing of the four cached GCS parts. Each `objects` entry contains `name`, absolute `pool_path`, integer `bytes`, and `sha256`. Names must occur in order from `q8/8865619b/6ed2c7aa_m400.tar.part00-of-04` through `part03-of-04`. The listed files must already exist within the pool. This build does not download them. The resolver hashes each file and the concatenated stream, then checks P's done marker. No guessed size or hash is accepted.

Supply `metadata` entries with `pool_path`, `bytes`, and `sha256` for each model/tokenizer/config text file absent from P's small archive. The model manifest supplies their expected hashes. The resolver refuses missing metadata. It reads P's `h_6ed2c7aa/m400/{DONE.json,e.json,r.json,s.tar}` and `x_ee227714/o/gcs_6ed2c7aa_m400.done`; it inventories `h.json` and `RP.json` when present. The export-only proof uses `e.json` and `r.json`.

```bash
python3 -I -s -B /project/community/jjyeung/okh7/x_90a20c41/q/b/resolve.py --pool /project/community/jjyeung/okh7 --listing /project/community/jjyeung/okh7/x_90a20c41/g.json --output /project/community/jjyeung/okh7/x_90a20c41/r.json
sbatch --chdir=/project/community/jjyeung/okh7/x_90a20c41/q --output=/project/community/jjyeung/okh7/x_90a20c41/o/%j.log --error=/project/community/jjyeung/okh7/x_90a20c41/o/%j.err /project/community/jjyeung/okh7/x_90a20c41/q/job.sh /project/community/jjyeung/okh7/x_90a20c41/r.json
```

Resource settings come from `kits/q/job.sh` and `kits/q/b/g.py`: general partition, one GPU, eight CPUs, 192 GiB requested memory, twelve hours. Memory and time sizing are GUESS. The GPU guard requires at least 80 GiB reported by CUDA; a nominal 80 GB device can fail that exact check. No real allocation or model fit was tested.

The job validates its seal, stages P's pinned venv/closure/inputs through P's staging functions, stages N's uploads and the export locally, and constructs P's original bwrap path mappings. Its caches and temporary files stay on the allocated node. It runs `b/a.py q`, then runs the room report independently of the proof result.

Read `x_90a20c41/o/JOB/RESULT.json` for `proof_rc` and `rooms_rc`. This wrapper deliberately retains GO=false. The accompanying `o.tar` contains the native `p/q/RESULT.json`, forward receipt when produced, logs, and room report when produced. Only the native admission result establishes ADMIT; shell success or room counts do not. Room cells retain counts and up to twenty example keys under the pinned K1, R0, and withheld-room rules (`proofs/operator/ROOMS.json` records the fixture result).

Seal, path, size, SHA-256, receipt schema, milestone, model metadata, and export-stream mismatches refuse with E-prefixed errors. Native admission keeps its own typed refusals, including capacity and component-evidence gates. `proofs/operator/RESULT.json` lists static pins unavailable here. P's staged pool inputs must resolve those pins, including any runtime-prepared stores; that complete real-input closure has not been verified on this node. A resolver success alone does not certify it.
'''
(B/'OPERATOR.md').write_text(operator)
text=['NO-GO — mode q refuses R1_POST_FILTER_CAPACITY_SHORTFALL:pose at both milestones; the real job needs complete eligible post-filter stores and a successful production audit.','',
'The source fixes and an unsubmitted Orchard proof kit are delivered. The fixture did not reach ADMIT. Production audit, final handover, N initialization from the export, and every-rank first forward/loss remain unproved. GO=false.', '',
f'The source seal is `{seal}` (`out/TREE_SEAL.json`). The delivery is `out/tree_rebuild_b20_{seal[:8]}.tar`; its bytes and SHA-256 are recorded in `work/build20/DELIVERY.json`.', '',
'The review findings are addressed as follows:', '',
'| Finding | Fix | Evidence |','|---|---|---|',
'| Pose receipt form | Authenticate the composite schema, ordered source/plan pins, division and model/teacher pins. The prepared reader binds child databases and complete order; filtering requires a unique valid subset. | `work/tree_r1/tests/test_r1_build20.py`; `work/build20/proofs/receipts/RESULT.json`; composite producer test in `work/build20/edges20.py`. |',
'| Official selection | Require the returned identity to name the hash of the artifact actually verified. Official DEFERRED selection refuses. | `test_selection_binds_returned_identity`; `work/build20/proofs/retained19/TESTS.json`. |',
'| Status-map tampering | Bind the full nine-slot map to pinned preparation bytes and its status digest. Missing, extra, altered, recordless and registry-conflicting VERIFIED slots refuse. Exports carry that binding, including descendants. | `test_guard_status_tampering`, `test_guard_preparation_and_records`, `test_export_binding`; `work/build20/proofs/edge20/TESTS.json`. |',
'| Staging omissions | Include component-row record `f7eaf7a7` and K1 list `43853165` in the inventory and hashed N uploads. | `work/build20/proofs/operator/STAGING.json`; `work/build20/UPLOADS.json`. |','',
'The before-control tests fail against the saved original functions. The repaired tree passes the focused regression and retained deferral/refusal/official-reader tests. Exact test totals and failures are in `work/build20/VALIDATION.json`; the source snapshots are in `work/build20/base/`.', '',
f'All {len(read("work/build20/proofs/mutations/RESULT.json"))} tree mutations and {len(read("work/build20/proofs/job_mutations/RESULT.json"))} job mutations were caught with passing controls (`work/build20/proofs/mutations/RESULT.json`, `work/build20/proofs/job_mutations/RESULT.json`). Current-source changed-statement coverage is {cov["observed"]}/{cov["total"]}; job-library statement coverage is {cov["job_library"]["observed"]}/{cov["job_library"]["total"]} (`work/build20/DELTA_COVERAGE.json`). The uncovered job branches remain a validation gap.', '',
'The real receipt scan hashes files under the supplied inputs, ext and fixtures trees. It calls the mode-q identity reader for every matching stream receipt it found. The full results and hashes are in `work/build20/proofs/receipts/RESULT.json`. These requested receipts are absent:', '']
for item in receipts['absent']:
    text.append('- `'+item['sha256']+'`: '+', '.join('/'.join(x[:2]) for x in item['uses'])+'.')
text += ['', 'The real prepared pose reader also refuses because child receipt `30612832` is absent. That refusal preserves authentication; this build does not claim a complete real P handover. A/C/Cprime effective-configuration comparisons pass (`work/build20/proofs/real/RESULT.json`).', '',
'| Fixture stage | Export-only milestone 400 | Checkpoint milestone 600 |','|---|---|---|',
'| Staging, persisted receipt, opener witness | PASS | PASS |',
'| Native preparation and routing composition | PASS | PASS |',
'| Card capacity | REFUSE: pose shortfall | REFUSE: pose shortfall |',
'| Production audit | NOT REACHED | NOT REACHED |',
'| Final handover and N initialization | NOT REACHED | NOT REACHED |',
'| Every-rank first forward and loss | NOT REACHED | NOT REACHED |', '',
'Sources: `work/build20/proofs/native/400/q/RESULT.json`, `work/build20/proofs/native/600/q/RESULT.json`, and their `twins/` receipts. The native fixture uses real producers/readers with synthetic RGB and metric labels, a tiny persisted HF model/processor constructor, CPU publication collectives, and a local frame host. Those boundaries are implemented in `work/build20/native20.py` and `native_assets20.py`. No capacity-sized population was generated.', '',
'The capacity preflight measured a minimum 382,952,000 bytes for the existing VQA, routing and pointing row payloads alone, excluding pose and producer duplicates, against an inherited workspace already exceeding 1.17 GB. The authorized workspace cap is 1.5 GB. The preflight refused before that write (`work/build20/proofs/capacity/RESULT.json`). The requested counts and their card source are recorded there. A larger authorized workspace or user removal of inherited outputs is needed to run this fixture as specified.', '',
'The focused suites pass. The packet suite has 200 passes and two failures, matching the prior documented floating-point JSON comparison and absent external attack decoder (`work/build20/proofs/final/packet/results.json`, `work/build20/packet.log`). The full frozen R2 suite was stopped by this build before output growth could violate the workspace cap; generator and legacy groups lack external inputs. No inherited pass total qualifies the current source (`work/build20/SUITE_RUNS.json`).', '',
'The preservation checks retain the step-544 `1d6eeb28` parent, weight_scale 0.04, the 601-row list, exclusions, card cells, and the unchanged native training/model functions (`work/build20/proofs/configuration/RESULT.json`, `work/build20/proofs/preservation/RESULT.json`).', '',
f'The proof kit is `work/build20/kits/q/`. Its {op["uploads"]} upload files total {up["total_bytes"]} bytes (`work/build20/UPLOADS.json`); the inventory includes every local path, opaque destination, size and hash. The kit seal is `{op["kit_sha256"]}` (`work/build20/proofs/operator/RESULT.json`). The kit was restaged from an empty destination and remains GO=false (`work/build20/RESTAGED.json`).', '',
'The job requests the general partition, one GPU with at least 80 GiB visible to CUDA, eight CPUs, 192 GiB memory and twelve hours. Memory and time sizing are GUESS (`work/build20/proofs/operator/RESULT.json`, `work/build20/kits/q/job.sh`). The local tests execute the resolver, real staging shell/heredocs, hash checks and room reader on a fake pool. Slurm variables and the bwrap execution boundary stand in; actual bwrap isolation, GPU execution and complete real P input closure were not checked (`work/build20/proofs/job/TESTS.json`, `work/build20/proofs/operator/NAMESPACE.json`).', '',
'The operator uploads the packaged files, supplies the offline GCS-part/metadata listing after the export lands, resolves the request, and submits the single job only after reviewing these gaps. Exact commands, output paths, result interpretation and refusals are in `work/build20/OPERATOR.md`. No job, network request or scheduler command was submitted by this build.', '',
'The kit file list below comes from `work/build20/proofs/operator/RESULT.json`:', '']
text += ['- `'+n+'`' for n in sorted(op['files'])]
text += ['- `BUILD.json` and `SHA256SUMS.txt` (upload inventory: `work/build20/UPLOADS.json`).', '',
'For the confirmation', '',
'Confirm the fixes against the independent review, resolve the missing real receipts and static pool pins, and complete the capacity-sized fixture, full frozen suite, uncovered job branches and real namespace/GPU proof before treating this build as GO. The report-only room census does not change admission. The delivery omits generated checkpoints, stores, frame sets, caches and repeated historical payloads; its manifest identifies the included evidence and source. The provided build-19 workspace remains the base for historical harness dependencies.', '']
(L/'out/BUILD20_REPORT.md').write_text('\n'.join(text))
(B/'STATUS.md').write_text('Build 20 is NO-GO.\n\nItem 1: source fixes, regression controls, mutations and available real receipt readers completed. Missing receipts are listed in proofs/receipts/RESULT.json.\n\nItem 2: native preparation passes; both milestones refuse R1_POST_FILTER_CAPACITY_SHORTFALL:pose. Capacity generation exceeds the authorized workspace budget and remains incomplete.\n\nItem 3: unsubmitted kit, resolver, upload inventory and operator commands built. Local staging/namespace-argument tests pass; actual bwrap/GPU and complete real-input closure are unverified.\n\nItem 4: focused tests and mutations pass; packet suite retains two failures; full frozen suite and job branch coverage are incomplete. Source sealed; packaging is in progress.\n\nUpdated '+stamp+'\n')
print('Report and operator commands written; seal '+seal)
