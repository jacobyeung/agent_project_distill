Packet C drivers are built for run `05b8ac69`, job `a15_cot_ap05b8ac69`, bundle `/project/community/jjyeung/okh7/i_7f1589c1`, and kit `/project/community/jjyeung/okh7/x_7f1589c1`. Training resumes A at step 200 and stops at step 600 on **advanced, four GPUs, 24 hours**. The CPU proof uses **bootstrap** by default, or **general**, with 48 CPUs, 800G RAM, no GPUs, and four hours.

The archive is `p_c60b9015.tar`, SHA256 `c60b901594843989b909cb785a5fdc9ad544ea0fdec8d78c63bf173e4f6e136c`. The config identity is `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74`. `packet_config.py` verifies the supplied archive digest, `CONT2_INVENTORY.json` after pins, `OPERATOR.json`, and the archive's exact `sums.txt` inventory. The frozen outer `out/SHA256SUMS` belongs to A and is not an authority for C. `PACKET_PIN_SOURCES.json` records the gate, wrapper, sums, and config-file digests.

The local fixture reached READY. The independent C review, deployed-kit certificate, fresh sessions, real CPU proof, donor slot, and written C launch GO remain operator gates. `rv1.sh`, `sc1.sh`, and `si1.sh` are inert until their builders receive the required inputs. No move-aside command is needed: C's bundle and kit must start absent.

Run these commands from `drv_c1`. The `orch` helper below is for the operator; this build made no remote connection or submission. Check `DRIVER_SHA256SUMS.txt` before running installer builders, which replace the three placeholders. Stop after an unsuccessful or uncertain operation; preserve its records and do not resubmit automatically.

```bash
cd /scratch/jjyeung/orch_n30/r1_ops/work/drv_c1
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
PY=/scratch/jjyeung/envs/p1cpu/bin/python
EVENTS=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
orch() { local file=$1; shift; timeout 300 bash "$OSSH" "bash -s -- $*" < "$file"; }
sha256sum -c DRIVER_SHA256SUMS.txt
```

Every checksum must report `OK`. Use the commands in this order:

| Order | Command | Expected result |
|---|---|---|
| 1 | `orch u1.sh` | `PASS outer SHA; 39 members; sums.txt exact inventory; files 0600`. |
| 2 | `orch q1.sh` | `PASS native receipt reused; native_unit_regeneration_executed=true`; selection `5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af`. |
| 3 | `"$PY" -B review_build.py` | `READY rv1.sh; nine-review chain pinned; final verdict GO`, or GO AFTER FIXES with explicit LOW fixes. `PENDING` means stop here. |
| 4 | `orch rv1.sh` | `PASS installed nine-review chain; final review_r1c1 accepted for packet C; no production GO granted`. |
| 5 | `orch ev1.sh`, then `orch evp1.sh` | `STARTED e0`; wait for `e0 rc=0` and four verified evidence records. Poll at most once per minute. |
| 6 | `orch dv1.sh`, then `orch dvp1.sh` | `STARTED d0`; wait for `d0 rc=0`, `status=READY`, C's identity, `missing_source_members=[]`, and `PASS b/ and code subdirectories 0500; no __pycache__`. |
| 7 | `orch scan1.sh > scan1.out` | The output binds C's archive, identity, run, and manifest. Obtain an independent complete content scan and `ANON_OK.json`. |
| 8 | `"$PY" -B cert_build.py ANON_OK.json --scan-record CLASSIFIED.json`, then `orch sc1.sh` | `READY sc1.sh`, then an independent CLEAN certificate installed with the exact manifest, scan, exemption, and all 39 external member pins. |
| 9 | `bash L1_mint.sh` | `PASS 20 fresh create-only sessions; mode 0600; URI contents withheld`. |
| 10 | `"$PY" -B session_build.py`, then `orch si1.sh` | Private installer READY, then `PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld`. |
| 11 | `orch pq.sh`, then `orch pr1.sh bootstrap` | Queue snapshot; sealed-kit checks; CPU sbatch argv with `--parsable -p bootstrap -t 04:00:00`; `SUBMITTED job_id=…`. Use `general` instead only if selected by the operator. |
| 12 | `orch pm1.sh`, then `orch f2.sh > proof_fetch.out` | C proof accounting and bounded proof JSON/log. Require completed PASS proof, `rc=0`, and `checks.resume_pointer.status=PASS`. `NOT_YET` means wait. |
| 13 | `orch go_submit_c60b9015.sh "$PROOF_JOB" "$GO_SHA"` | A's scheduler state; verified step-200 slot-record preflight; GO written or byte-equal reuse; `SUBMITTED training_job=… proof_job=… advanced gpu=4 time=24:00:00`. |
| 14 | `orch mon.sh` | Read-only C proof/training queue and accounting, redacted bounded logs, and retained training record. Poll at most once per minute. |

Before step 13, set `PROOF_JOB` to the exact ID from step 11. Set `GO_FILE` to the written, identity-bound **C** ORCH GO file, then compute `GO_SHA=$(sha256sum "$GO_FILE" | cut -d' ' -f1)`. The wrapper's stdin usage is `bash -s -- <PASSING_PROOF_JOB> <sha256 of ORCH GO file>`. Keep `proof_fetch.out`, session JSON, mint logs, and `si1.sh` private; the session installer contains capabilities.

The final review must be `events/review_r1c1/REVIEW_VERDICT_R1C1.md`. Its `Packet C:` line must declare GO, or GO AFTER FIXES with only explicit LOW, nonblocking fixes. C's section must name the full archive digest or config identity. Missing, stale, negative, ambiguous, or above-LOW final reviews refuse. Packet-A reviews `review_r1p` through `review_r1p8` remain eight antecedents and cannot authorize C. The builder prints remaining LOW fixes. The evidence worker independently checks all nine review texts and hashes.

C's native selection equals A's. `q1.sh` reuses the authenticated native receipt and regenerates the unit projection with the sealed selector. Data records keep `record_key=69d2930d`; C's bundle, kit, run, proof, logs, slots, and export destinations use C's fresh identity. Sessions cover `05b8ac69_{m400,m600,mstop,mstopB,mstopC}`, four parts each. Minting refuses existing objects, fallback exports, sessions, or an uncertain mint attempt. A's sessions are never reused.

`pr1.sh` rejects every queued job with C's name, including held duplicates, and every previous local submission attempt. A's training `171377`, A's proof `171356`, and the eight held `jjy_*` jobs do not block C's CPU proof. It writes `job.id` only after parsing `sbatch --parsable`. `pr2.sh` shares the same guard and markers; it is not a second submission route.

`go_submit_c60b9015.sh` pins C's archive, `s.sh`, `sums.txt`, and `jb.sh`; it calls the unchanged sealed PASS-proof gate. The wrapper binds the proof to C's `job.id`, original parsable sbatch receipt, PASS JSON, and completed accounting. Its queue guard rejects any other C job. Its accounting guard permits only that proof ID under C's name. Training locks and create-only markers reject repeated or uncertain attempts. The GO fields match C's sealed gate, omit canary authorization, and permit only byte-equal reuse. The training ID comes from the sealed gate's sbatch output.

The wrapper prints A's queue/accounting state and refuses while A's training may still hold the advanced allocation. Pending or held unrelated jobs do not hold that allocation. It reads only `A.json` and `B.json` under `okh7/r/673bc60f` and requires a record with boolean `verified=true` and integer `step=200`. This preflight does not read the large donor archive. C's sealed `b/c0.py` verifies the full donor binding, archive, checkpoint, optimizer state, and shards in the training allocation. A's donor kit and slots remain read-only.

Local evidence is in `test_*_c1.txt`, `test_results_c1_ready.txt`, `antecedents_c1.json`, and `TEST_STORAGE_C1.json`. Tests cover READY derivation, both sealed proof partitions, code permissions, review isolation, installers, selection/unit regeneration, REMOVE integrity, mint absence checks, queue exceptions, training refusals, GO reuse, read-only monitoring, and shell/Python syntax. The fixture uses synthetic approvals and two H1 source sentinels; it does not attest live data, donor availability, scheduler capacity, or production admission. The new test scratch is below 300 MB, counting shared hardlinks once. Copied predecessor test artifacts are outside that measurement and remain untouched.
