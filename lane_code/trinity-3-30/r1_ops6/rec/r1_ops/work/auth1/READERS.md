# Authority for job 171377

`4.train.json` changes exactly four values from the pinned live authority: `modes` becomes `["p","t","u"]`, `new_gpus` becomes `{"p":0,"t":4,"u":4}`, `partition` becomes `"advanced"`, and `scope` becomes `"One four-rank canary for 171377 and concurrent mode-p CPU proof; continuation uses latest."` The JSON retains the live file's sorted keys, compact separators, and final newline. Every other value remains identical, including dates, source revision, configuration identity, conditions, and production-GO flags. `diff.json` records the complete comparison.

| Reader | Authority fields and checks on p/t/u |
| --- | --- |
| `b/g.py:82–88` | `allow_until_utc` must be timezone-aware, at least 2026-11-22 UTC, and later than now; `source_revision` must equal `k/0.json.commit`; `modes` must contain the requested mode. |
| `b/i.py:44–96` (`authorize`) | `arm` must contain the requested arm, have no duplicates, and use known arms; `modes` must contain a known operation. `source_revision` must match for non-final configurations; this final configuration is checked by g.py. `allow_until_utc` must be timezone-aware and unexpired. `new_gpus` must grant the operation's required count (p=0, t/u=4 here), with integer counts; `other_running_and_pending_gpus` must be a nonnegative integer; `gpu_cap` must be an integer in 1..128 and cover all authorized arms plus other GPUs. t/u also require Slurm nodes=1 and GPUs/node=4, and verify the derived admission through d.effective. |
| `b/x.py:14–27` (`ready`, called by authorize) | u reads `resume`: `latest` is accepted; another value must be an absolute path+sha256 binding. No additional authority fields for p/t. Configuration input/preparation bindings are checked independently. |
| `b/i.py:136–166` (after authorize) | `new_gpus` supplies the count written into `o/171377.3.json`. The receipt also records derived configuration identity, job ID, and verdict GO. No further authority-file read in the parent. |
| `b/w.py:11–14, 88, 109–114, 177–181` | Each worker calls authorize again. `new_gpus` must match the parent's allocation receipt. u reads `resume`, scans an explicit binding when it is not `latest`, and requires a nonempty continuation choice. t/u pass `milestone_gate` into the trainer; its existing null value is retained. p adds no fields. |
| `student_pilot/carrier_c1_run.py:2856–2860` | Reads the separate allocation receipt supplied by w.py, not k/4.json: checks `config_sha256`, `new_gpus`, `job_id`, and `verdict`. The trainer receives resume/milestone settings from w.py; it never reopens k/4.json. |
| `b/a.py:14–25` | Checks the SHA256SUMS.txt digest of the entire k/4.json byte sequence and exact b/k inventory. It does not interpret authority fields. Job startup and r.sh call it before admission; the parallel proof also needs the original bytes. |
| `b/r.sh:25–39, 50–86`; `job.sh` | Invoke a.py, g.py, and i.py; do not parse k/4.json themselves. The parent performs its t/u g.py check after the admission child exits. |
| `b/c.sh:398–438` | `tk_nx` copies b/, k/, the manifest, and certification to the node-local kit. `tk_persist_small` and `tk_persist_exports` do not read k/4.json or its fields. |
| `jb.sh` | No authority-file read. Export-session checks, binding mirror, checkpoint restoration, archive verification, GCS fallback, and slot publication read their own receipts/configuration, not k/4.json. Inspected fixture_p7/jb.sh is byte-equal to cert_p5_eyrowmar/b/jb.sh, SHA256 b6a1e4c8f4c0a8fce029233575d082fae69ba018a311288dc8391493efa4648f. |

No inspected p/t/u reader uses authority `wall_seconds`, `partition`, `allowed_partitions`, `written_authorization`, or `written_authorizations`. Therefore `wall_seconds=14400` remains unchanged and no written-authorization fields are added. `partition` changes as explicitly requested. The launch slot and both batch wrappers independently specify 46800 seconds / 13 hours; the configuration's recipe duration is separate. The supplied GO file was read and its SHA256 verified as `4c2fa9600c9515c300d90a9e349e4766f50c13c013b0012f2b1628257e08ef33`: `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/r1_ops/20261118T0044Z_ORCH_RULING_canary_launch_parallel_proof.md`.

`test_authority.out` records the actual g.check and authorize results: the live authority refuses t with “Written slot authorization is absent or expires too early” and “Operation not authorized”; the new authority passes t and p. Both authorities pass p. The new authority also passes u authorization, all four worker authorization calls, and t/u dispatch; an incorrect GPU count refuses. Validators and launch bytes remain unmodified. Tests use synthetic admission receipts and redirect absent Orchard filesystem locations into this lane. They exercise admission validation, but do not establish real admission success or train on GPUs. No CUDA stub was needed.

`test_scripts.out` records a successful install/restore round trip, exact byte recovery, permissions 0700/0600, an unchanged k/ inventory, and refusals for repeated actions or a wrong live digest. The tests execute the scripts' embedded code using the permitted local Python and substitute only the target root. `bash -n` passes for both scripts. The scripts themselves use Orchard's `/usr/bin/python3`; neither script was executed against Orchard.

Run the standalone `install.sh` once on Orchard with no competing authority writer: `bash /path/to/install.sh`. It requires the original digest, exclusively creates `/project/community/jjyeung/okh7/auth_x69` at 0700, writes its byte-exact `4.p.json` backup, and publishes a 0600 temporary file from the kit root. It preserves the displaced original outside k/, checks destination absence before ordinary rename, and does not use renameat2 flags or deletion. A failed rename leaves recovery files for operator inspection; do not retry blindly.

Expected install output:
```text
2f450bfaa65e6ae0dcfbd1c790fdeb374b9356a9d2b48f5f4ba9835f127d2353  /project/community/jjyeung/okh7/auth_x69/4.p.json
a9fbd4e28f029d498e04d1bd943bd56454e143a66b846470e83dc2bd07961ed3  /project/community/jjyeung/okh7/x_69d2930d/k/4.json
INSTALLED 171377; restore after all four workers pass authorize, before the CPU inventory check.
```

After all four workers have passed authorize, run `bash /path/to/restore.sh --all-workers-authorized-171377`. This argument records the operator's timing assertion; the script does not query the job. The parent's `171377.3.json` alone does not prove all workers have authorized. Confirm all-rank progress or an actual completed training step. Restoration changes the shared kit; the staged node-local kit remains available to the running workers. A later job/reentry requires its own authority installation.

Expected restore output:
```text
a9fbd4e28f029d498e04d1bd943bd56454e143a66b846470e83dc2bd07961ed3  /project/community/jjyeung/okh7/auth_x69/4.train.json
2f450bfaa65e6ae0dcfbd1c790fdeb374b9356a9d2b48f5f4ba9835f127d2353  /project/community/jjyeung/okh7/x_69d2930d/k/4.json
RESTORED 171377; original bytes restored; no auxiliary files were written into k/.
```

The report applies no-archaeology; it retains no borderline process-history statements. All deliverables and test writes stay inside this lane. No SSH, Orchard access, Git, GPU use, or deletion was performed. Independent launch review and operator execution remain outside this local build.
