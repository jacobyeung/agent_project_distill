import hashlib,json,pathlib,shlex
B=pathlib.Path(__file__).resolve().parents[1];A=B.parents[1];O=B/'out'
def load(p):return json.loads(p.read_text())
F=load(O/'FAMILY.json');C=load(O/'BASELINE_CONFIG.json');P=load(O/'BASELINE_prepare_config.json');S=load(O/'SIZING.json');sel=load(O/'ITEM_SELECTION.json')
worker=C['worker'];artifact=load(A/'work/from113/work/obj/m544_artifact.json')
rest=['# Restoration admission','', 'The candidate training closure is missing. An export contains the artifact and tensors; it does not supply the authenticated preparation configuration and receipts that this backend requires. The direct-reader completion receipt authenticates transport, not the missing training metadata.', '', '| Check | Accepted value | Candidate requirement |','|---|---|---|',
'| Artifact file SHA256 | `'+worker['artifact']['sha256']+'` (`BASELINE_CONFIG.json`) | Derived after complete tar verification; exact step/run and artifact pin required |',
'| Prepared config file SHA256 | `'+worker['config']['sha256']+'` (`BASELINE_CONFIG.json`) | Candidate config file, not a path substitution into accepted bytes |',
'| Canonical training config identity | `'+artifact['config_sha256']+'` (`BASELINE_prepare_config.json`) | Recompute with the unchanged trainer.identity; equal artifact and preparation config_sha256 |',
'| Production data receipt SHA256 | `'+worker['data_receipt']['sha256']+'` (`BASELINE_CONFIG.json`) | PREPARED, nonsynthetic, real frames verified; exact config/preparation pins |',
'| Preparation receipt SHA256 | `'+P['preparation']['sha256']+'` (`BASELINE_prepare_config.json`) | Verify architecture, streams, layout, route policy and scene exclusions against candidate config |',
'| Source seal file SHA256 | `'+P['code']['sha256']+'` (`BASELINE_prepare_config.json`) | Authenticate actual staged source files and candidate seal bindings; fixed backend source cannot drift |',
'| Run seal SHA256 | `'+artifact['source_seal']['sha256']+'` (supplied `work/from113/work/obj/m544_artifact.json`) | Check candidate source-seal/config binding and export seal unchanged |',
'| Init specification | Derived by `evalpath/runtime.py:30` in supplied trainer | Bind candidate artifact and every trained group; exact trained tensor loading remains required |',
'| Own-head scale and gravity | Accepted manifest in `BASELINE_CONFIG.json` full projection | Recompute through the unchanged geometry kernel with the candidate heads; publish the new manifest and receipts |','',
'`guard_backend.authenticate_candidate` retains `read_runtime.prepared` and `runtime.check_init_spec`. `Session` uses the authenticated C8r restore, parity and geometry functions. Each checkpoint needs a fresh process because the sealed gravity guard installs once and tracks capture verdicts. The production process coordinator is not implemented.', '',
'`guard_export.stage` first binds the plain-text completion record to the prepared plan, checks whole-archive size and digest, normalizes only the record container to JSON, then calls the unchanged reviewed `stage_export` with full checking. The reviewed file and checker are shipped byte-for-byte. The candidate wrapper is not yet connected to C8r job staging.', '',
'C8r can validate ordinary milestone member roots and whole archives. Its production transport descriptor, prepared configuration, artifact pin and ancillary receipts are fixed to the accepted run. The reviewed stager admits the candidate milestone layout, but its namespace/checker bootstrap must be connected to the new job; copying that module alone does not finish the integration.', '',
'`PIN_CLASSIFICATION.json` records the baseline values. No candidate hash, config identity, source seal, init specification or prepared geometry value has been invented. They remain unavailable until the candidate closure and export are admitted.','']
(O/'RESTORATION.md').write_text('\n'.join(rest))
# Disk bound uses original full archive sizes, not the small local rehearsal substitutes.
a=C['assets'];exp=C['transport']['archive_bytes']
disk=2*(a['runtime']['bytes']+a['numpy']['bytes']+a['closure']['bytes']+a['trainer']['bytes']+a['base']['bytes'])+4*exp+2*sum(x['bytes'] for x in a['small_objects'])+sum(x['bytes'] for x in a['depth'])+4*10**9+100*10**9
S['disk_estimate_bytes']=disk;S['disk_assumptions']='Retain both tar and expanded bytes for both exports, base/runtime archives and expansions, shared small objects, depth, frames/output allowance and local reserve. Candidate archive bytes must replace the reference-sized estimate at preparation.'
S['local_build_cap_bytes']=6*10**9;(O/'SIZING.json').write_text(json.dumps(S,indent=2,sort_keys=True)+'\n')
(O/'SIZING.md').write_text(f'''# Time and storage

The requested wall limit is `{F['time_limit']}` (`SIZING.json`). The estimated need is {S['need_seconds']:.1f} seconds, with {S['margin_seconds']:.1f} seconds of margin (`SIZING.json`).

The estimate includes shared staging, another export transfer and header check, complete geometry preparation for both exports, measured native item time, the selected proof items and conservative load/parity residuals. Canary rows are reused. The accepted native item total is {S['native_item_seconds']:.1f} seconds (`SIZING.json`, sourced from `{A}/work/ret544/native/R1.json`). Scripted records do not measure a second model decode, so halving the paired wall time is unsupported.

The provisional disk estimate is {disk} bytes (`SIZING.json`). It includes retained archives, expanded files and reserve. Candidate size and free job-local space must be checked before staging. No large runtime, base or export archive was expanded here.

The local build cap is {S['local_build_cap_bytes']} bytes (`SIZING.json`). Final measured use is recorded in `BUILD_SIZE.json`. Live Orchard free space, transfer throughput and candidate decode duration were not checked.
''')
# Exact operator commands are presented as blocked, never as an executable release.
lines=['# Operator run sheet','', '**NOT READY.** `packet.py packet` intentionally refuses to emit a batch while integration is incomplete. The commands below define the intended operator interface. They do not authorize upload or submission. Read `RELEASE_BLOCKERS.json` first.', '', 'The candidate metadata manifest must contain pinned config, data_receipt, preparation, source_seal and inventory files. The candidate closure is absent from the supplied inputs. Never substitute the accepted training metadata.', '', 'Local validation:', '```sh', 'cd '+str(B), 'export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1', 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/tests/test_g1.py', 'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/tests/test_stage.py','```','', 'New-object upload commands, held until release blockers and independent review are resolved:', '```sh']
for name,field in [('code_g1.tar','code'),('inputs_g1.tar','inputs')]:
 lines+=['gcloud storage cp '+shlex.quote(str(O/name))+' gs://cmu-gpucloud-jjyeung/'+F[field]['name'],
         'gcloud storage objects describe gs://cmu-gpucloud-jjyeung/'+F[field]['name']+' --format=json']
lines+=['```','', 'Cloud generations remain `PENDING_UPLOAD` in `FAMILY.json`. Record actual generation, size and digest, reseal the family and obtain review on that family. Do not replace a placeholder without checking uploaded bytes.', '', 'Orchard neutral-copy commands are copied verbatim below from `NAMING.md`:','']
naming=(O/'NAMING.md').read_text();lines.append(naming[naming.index('```sh'):])
lines+=['', 'Milestone commands on Orchard after the missing metadata is staged under the neutral pool. Every token below is distinct (`OPERATOR_TOKENS.json`). Each destination must be fresh. These draft prepare/packet calls cannot produce a runnable batch in the current release.', '```sh', 'cd /project/community/jjyeung/okh7/8c9d2e74/g1']
tokens={str(step):hashlib.sha256(('g1-review-build-'+str(B)+'-'+str(step)).encode()).hexdigest()[:16] for step in (200,400,600,800,1000)}
(O/'OPERATOR_TOKENS.json').write_text(json.dumps(tokens,indent=2)+'\n')
for step,token in tokens.items():
 lines+=[f'# Candidate m{step}; commands remain blocked by this family.',
 f'/usr/bin/python3 -I -s -B guard_kit/packet.py prepare --family FAMILY.json --done /project/community/jjyeung/okh7/x_f5c353f7/o/gcs_359fcc3c_m{step}.done --step {step} --metadata /project/community/jjyeung/okh7/8c9d2e74/m{step}_meta.json --token {token} --out plans/{token}',
 f'/usr/bin/python3 -I -s -B guard_kit/packet.py packet --config plans/{token}/CONFIG.json --review REVIEW.json --order ORDER.md --out packets/{token}',
 f'# After a completed, reviewed packet builder exists:',
 f'# sbatch --partition=general --gres=gpu:1 --ntasks=1 --nodes=1 --cpus-per-task=16 --mem=200G --time={F["time_limit"]} --job-name=a15_cot_ap{token} packets/{token}/BATCH.sh']
lines+=['```','', 'No batch file exists and no sbatch command is currently runnable. Resources belong on the command line. Input tars must have no hard-link members; the new archives pass this check (`CODE_MANIFEST.json`, `INPUT_MANIFEST.json`). Existing large Orchard archives were unavailable for inspection.', '', 'Governed fetch, held for the operator:', '```sh', '# Run on Trinity; registration must succeed before opening any stream.', '/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B /data3/jjyeung/orch_n13_20261026/io_governor/register.py --tier 3 --allow-resume', '# Then use the governor-issued stream command for the published return object.', '# Intended source: gs://cmu-gpucloud-jjyeung/q8/8c9d2e74/<token>/result.tar.gz', '# Intended destination: '+str(B)+'/out/fetched/<token>/result.tar.gz','```', '', 'The named governor script is absent on this node. Its remaining CLI arguments and the new return publisher are not validated, so this sheet does not invent a runnable governed stream. Fetch only after registration and verify the return receipt size and SHA256. No fetch ran here.', '', 'Ledger line format for `work/ORCHARD_LEDGER.jsonl` (append only after actual submission; never record a draft as submitted):', '```json', '{"utc":"<UTC>","job":"<actual Orchard job>","token":"<fresh hex>","step":"<candidate step>","run":"359fcc3c","done_object":"<exact object>","done_bytes":"<whole tar bytes>","done_sha256":"<whole tar SHA256>","family_sha256":"<reviewed family SHA256>","plan_sha256":"<sealed plan SHA256>","status":"SUBMITTED","order_sha256":"<exact ORCH order SHA256>"}', '```','']
(O/'RUN.md').write_text('\n'.join(lines))
(O/'rehearsal/RUNBOOK.md').write_text(f'''# Rehearsal runbook

The whole-worker rehearsal is incomplete. `namespace.stderr` records the sandbox refusal; `records_pass/RESULT.json` explicitly marks the recorded-row run as a fixture with no model decode. It is not evidence that production CONFIG works with transport-only changes.

Run the completed local component checks with the required interpreter:

```sh
cd {B}
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export XDG_CACHE_HOME="$PWD/work/cache" HF_HOME="$PWD/work/cache/hf" TRITON_CACHE_DIR="$PWD/work/cache/triton"
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/rehearsal/run_records.py --out out/rehearsal/operator_records
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B out/rehearsal/run_records.py --out out/rehearsal/operator_mismatch --mismatch
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B work/run_c8r_tests.py
```

Use fresh output destinations. The recorded-row run writes proof and canary receipts, merges only the native arm, verifies a local archive copy, and invokes the unchanged report on its fixture R1 against itself. The mismatch changes a reference token and must preserve PROOF while producing no candidate arm (`records_mismatch/RESULT.json`).

The supplied boundary stand-ins are at `{A}/work/from113/builds/02_c8r/out/rehearsal/cpu_boundary.py`. Their numpy/scipy and extra import roots are `{A}/work/from113/work/np226` and `{A}/work/from113/work/pyextra`. Insert them explicitly under isolated Python. The completed C8r staging assets are at `{A}/work/from113/builds/01_c8/work/rehearsal_assets/d03de829ae52386f`.

After the candidate training closure and production coordinator are implemented, an operator outside this sandbox must run stage, prepare, historical proof, candidate canary/read, merge, admission, publish, fetch and report using the same sealed production CONFIG. Only transport and the documented model boundaries may differ. Use separate checkpoint processes because the sealed guard installs once.

There is no complete G1 whole-worker command to give yet. Reusing C8r's old harness unchanged would alter CONFIG and exercise its paired workflow; it would not satisfy this task. The namespace failure is only one blocker, not the reason to claim that missing integration is complete.
''')
