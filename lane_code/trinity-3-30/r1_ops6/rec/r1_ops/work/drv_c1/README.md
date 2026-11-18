Packet C drivers (`r1_drvc3`) pin `p_08f3a7b2.tar`, SHA256 `08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd`. C uses run `05b8ac69`, job `a15_cot_ap05b8ac69`, bundle `okh7/i_7f1589c1`, kit `okh7/x_7f1589c1`, and config identity `6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74`.

Training resumes A at step 200 and stops at 600: advanced, four GPUs, 24 hours. The proof uses general, zero GPUs, 48 CPUs, 800G, four hours. `pr1.sh` refuses bootstrap for account mt01 and accepts `--hold`. The rehearsal uses the exact CONT4 command: general, orchard-community-0, zero GPUs, four CPUs, 32G, 30 minutes.

The build passes local fixtures. The independent final review `events/review_r1c3/REVIEW_VERDICT_R1C3.md` grants GO for this exact archive. `rv1.sh` is ready; `sc1.sh` and `si1.sh` remain inert until their builders receive valid inputs. Proof, rehearsal, and training guards reject unexpected top-level kit entries that could shadow Python imports. The allowed inventory includes the private `sess.json` installed by this sequence. The eleven-review chain includes r1p–r1p8, r1c1, and r1c2 as antecedents. The final review must explicitly approve Packet C and bind its archive digest or config identity. Conditional approval accepts only explicit LOW fixes.

These commands are for the operator. The build made no SSH connection, Orchard call, live mint, or submission. Keep session files and installers private. Stop on failed or uncertain operations; retain all markers and never resubmit automatically.

```bash
cd /scratch/jjyeung/orch_n30/r1_ops/work/drv_c1
umask 077
unset PYTHONOPTIMIZE PYTHONPATH PYTHONHOME
export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
PY=/scratch/jjyeung/envs/p1cpu/bin/python
ROOT=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30
OSSH=$ROOT/tools/ossh.sh
orch() { local file=$1; shift; timeout 300 bash "$OSSH" "bash -s -- $*" < "$file"; }
sha256sum -c DRIVER_SHA256SUMS.txt
```

Run the following sequence. Poll workers and jobs no more than once per minute. The checksum list covers the shipped state; installer builders intentionally replace their pending scripts.

| Order | Command | Expected output or condition |
|---|---|---|
| 1 | `orch m1.sh` | `PASS moved aside /project/community/jjyeung/okh7/i_7f1589c1.f172180 /project/community/jjyeung/okh7/x_7f1589c1.f172180`. |
| 2 | `orch u1.sh` | `PASS outer SHA; 40 members; sums.txt exact inventory; files 0600`. |
| 3 | `orch q1.sh` | Authenticated native receipt and `native_unit_regeneration_executed=true`. |
| 4 | `"$PY" -B review_build.py`, then `orch rv1.sh` | `READY rv1.sh`, then `PASS installed eleven-review chain`. Stop at PENDING. |
| 5 | `orch ev1.sh`, then `orch evp1.sh` | `STARTED e0`; wait for `e0 rc=0`. |
| 6 | `orch dv1.sh`, then `orch dvp1.sh` | `STARTED d0`; wait for `d0 rc=0`, READY, sealed p/t/u authority, and b/ directories at 0500 without bytecode. |
| 7 | `orch scan1.sh > scan1_c3.out` | Current archive, config, manifest, and external-member inventory. Obtain an independent complete scan and certificate. |
| 8 | `"$PY" -B cert_build.py ANON_OK_C3.json --scan-record /absolute/path/CLASSIFIED_C3.json --scan-output scan1_c3.out`, then `orch sc1.sh` | `READY sc1.sh`, then independent CLEAN certificate installed. |
| 9 | `bash L1_mint.sh` | `PASS 20 fresh create-only sessions; mode 0600; URI contents withheld`. |
| 10 | `"$PY" -B session_build.py`, then `orch si1.sh` | Private installer READY; `PASS installed sess.json mode 0600; 20 fresh destinations`. |
| 11 | `orch pq.sh`, then `orch rh1.sh` when the ruling permits the general slot | `SUBMITTED rehearsal_job=…; never a PASS proof`. This seals general authority into fresh `a4.json`. |
| 12 | `orch rhf.sh > rehearsal_c3.out` | Inspect `REHEARSAL_OK`, rc 0 and step results. NOT_YET means wait; REHEARSAL_FAIL means stop. |
| 13 | `orch pr1.sh general --hold` | `PASS history: FAILED 172180 and rejected bootstrap only`; successful rehearsal required; `SUBMITTED job_id=…`. Set PROOF_JOB to this exact ID. |
| 14 | At A's end, `orch pre1.sh "$C_INPUTS" > pre1_c3.out` | Real step-200 slot/archive/manifest/shard verification; equal/different for each stream and family. Require final `PASS REAL A resume pointer and C/A preparation populations equal`. |
| 15 | Compute the ruling SHA as below; `orch go_submit_canary_08f3a7b2.sh "$PROOF_JOB" "$GO_SHA"` | A has released advanced; new proof is PENDING/RUNNING on general; canary gate accepts admission 172180; `SUBMITTED training_job=… proof_job=… advanced gpu=4 time=24:00:00`. |
| 16 | `orch mon.sh` | Read-only C proof/training queue, accounting, bounded redacted logs and retained training record. |
| 17 | Release the held proof only after the step-200 direct read finishes; then `orch pm1.sh` and `orch f2.sh > proof_c3.out` | Proof remains separate from training. Require completed PASS, rc 0 and resume_pointer PASS for proof completion. |

```bash
GO_FILE=$ROOT/events/r1_ops/20261118T0842Z_ORCH_RULING_C_canary_and_general_order.md
GO_SHA=$(sha256sum "$GO_FILE" | cut -d' ' -f1)
test "$GO_SHA" = 31f5e70ca014a370913115e124290805744e5947790e8d2463e5b0225130aa89
# After the step-200 direct read ends, release only the recorded held proof:
printf 'TZ=UTC scontrol release %s\n' "$PROOF_JOB" | timeout 300 bash "$OSSH" 'bash -s'
```

General-slot order is binding: reader 172456; step-100 direct read only if it leaves by 12:45Z; step-200 direct read first; C proof; routed reads. A pending/held proof satisfies the canary gate. The proof must not occupy general from 12:45Z until the step-200 direct read finishes. Schedule the short rehearsal within that same ordering. The wrapper does not infer that another lane's direct read has finished.

`pre1.sh` runs read-only on the Orchard login CPU. It streams the selected verified A slot once, hashes every checkpoint payload, and checks its binding and manifest against C's sealed continuation policy. It compares A's archived `inputs/data_receipt.json` and pinned `prepared/type_mix.json` with C's retained preparation. It does not deserialize model tensors or extract an archive.

Set `C_INPUTS` to a login-visible preserved inputs directory from proof 172180. Its original node-local location is `/tmp/jjyeung/p_05b8ac69_172180/tmp/jjyeung/a_05b8ac69/runs/05b8ac69/inputs` on orchard-community-0. That is the default argument, but login access may require the operator to preserve those small receipt files, including their relative prepared paths, on shared storage. The pinned proof log establishes stream counts; it has no family census. Missing C receipts cause a refusal, never an inferred family equality. Preserve the staged root for the rehearsal as CONT4 requires.

`m1.sh` accepts only FAILED 172180, checks the old archive/member inventory and failed receipt, and refuses any queued 172180 or same-name job. It preflights both destinations and retains inodes during same-filesystem moves. It uses RENAME_NOREPLACE, with the requested EINVAL fallback to `os.rename` after a fresh absence check under the held proof lock. Inspect partial state manually after any error. It moves only the bundle and kit; node-local staging remains available.

The moved kit retains its 20 old sessions. `L1_mint.sh` uses packet-specific local files `sess_05b8ac69_08f3a7b2.json`, `mint_05b8ac69_08f3a7b2.started`, and `mint_05b8ac69_08f3a7b2.private.log`. It checks destination objects and fallback exports, then mints 20 new capabilities. It never reads the moved kit's sessions. `si1.sh` creates only the new kit's sess.json.

The canary wrapper fixes ADMISSION_JOB=172180 and ADMISSION_KIT=`/project/community/jjyeung/okh7/x_7f1589c1.f172180`. It pins the ruling SHA and calls the sealed gate with its authenticated old admission evidence. Same-name accounting permits only FAILED 172180 and the new proof ID. Rehearsal IDs cannot serve as proofs. Training locks and create-only markers preserve failed/uncertain attempts. The gate's canary receipt records gate acceptance, not successful allocation.

For completed-PASS mode, use `orch go_submit_08f3a7b2.sh "$PROOF_JOB" "$GO_SHA"` instead of the canary submission, after a completed PASS proof and applicable separate written GO. Both wrappers share training markers; never invoke both for the same deployment.

Follow the ruling's kill conditions: pooled harm STOP, a protected outcome's second failure, admission differing from 172180, or failed early-loss checks. These drivers report state; they do not decide those outcomes or cancel A's job 171377.

`result_c3_*.txt` and `VALIDATION_C3.json` record local validation. Tests use scheduler/gate stubs and synthetic checkpoint/preparation data. Authority, proof sealing, and scan tests reuse the existing local READY fixture because the sealed derivation/config bytes are unchanged. They do not certify Orchard state, real populations, donor availability, or production approval. Exact-byte evidence includes `f172180.proof.json` and `f172180.proof.log`; the separately formatted `p172180.proof.json` has a different digest and is not the gate's receipt pin.
