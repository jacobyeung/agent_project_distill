These drivers prepare the final R1-P packet for one CPU-proof submission. The production-form fixture reaches READY, and the independent three-review chain ends with review_r1p3 GO on the exact final archive. Production GO remains false; the operator still needs Orchard evidence, independent content certification, fresh sessions, and the CPU proof.

The work directory is `/scratch/jjyeung/orch_n30/r1_ops/work/drv`. Run local builders there with `/scratch/jjyeung/envs/p1cpu/bin/python -B`; Trinity's default `python3` is 3.6 and cannot run the packet's complete test path. Orchard scripts use its `python3`, as the packet specifies.

The fixed bindings are:

| Item | Binding |
|---|---|
| Bundle | `/project/community/jjyeung/okh7/i_c5f3847d` |
| Derived kit | `/project/community/jjyeung/okh7/x_c5f3847d` |
| H1 source | `/project/community/jjyeung/okh7/x_3fdda0fb` |
| Actual Orchard source manifest | `661ccd85b7a8f1afd25297869dc3a28539e64a3a0ab9a74ee928c0c5ab8a66c3` |
| Operator archive | `p_c5f3847d.tar`, 12,206,080 bytes, 31 members |
| Outer SHA256 | `888027436a99cfec360959c46f4271222e4c029f5d36eb9870fea4f669231029` |
| Config identity | `d8b03fd14db01af4def4a0cfd9a49d16ec492d9a3c6b0c56977f7f22b79f705a` |
| Tree | `5e1514ef9d91bee8a1623e0e9db4844d5916a0836da953302413a212b23fe8b8` |
| Job | `a15_cot_ap26cc98b7` |

`packet_config.py` reads the frozen `snap_d8b03fd1/out/{R1P_PACKET.md,SHA256SUMS,BINDING.json,OPERATOR.json}` and verifies the archive and every inner member. `PACKET_PINS.json` records the resulting pins. `build_drivers.py` renders the scripts and copies the final `e.txt` from that archive. Its source helper files use `@NAME@` placeholders; execute the generated scripts. The final `d.py` SHA is `40c7908b891246e09bdd1878b1a54f039a00dfaa340362849a722ce5a8269f06`.

The independent verdicts are `events/review_r1p/REVIEW_VERDICT_R1P.md`, `events/review_r1p2/REVIEW_VERDICT_R1P2.md`, and `events/review_r1p3/REVIEW_VERDICT_R1P3.md` under `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. Fix rounds 4–7 connect the antecedent reviews to the final review. `review.json` names all three reviewers and preserves their verdict hashes. The evidence worker revalidates the uploaded review texts against this chain.

**Native selection choice:** reuse H1's authenticated 03:50Z regeneration. The valid `NATIVE_RECEIPT` is `i_1be16f28/q_6c18a2bf/o/native/receipt.json`, SHA256 `2e25a01d943cc910f58260255ae5d2943fbbee2b7114f7d86e280c509e321f68`. Neither the EQUAL report nor `d_eac5f9f01587803b.json` is a raw receipt. H1's `build/q.sh` runs native `s1_pool.prepare`, which retains that raw receipt and its ordered-index files. R1 changes only the permitted implementation files and room-source projection. `q1.sh` pins the EQUAL report (`e48ab85b…`), raw receipt and parent selection, then runs the unchanged `q.py` with `--implementation BUN/j.json --code-record BUN/c.json`. It rehashes every projected native index and checks all non-room entries. The final selection must hash to `5cf172c4c3e8c391920deb78a1e52396f1b05b9326b3e41fb7ae86d30a25120e`. A missing or altered retained receipt fails closed; the driver does not launch a substitute native run.

**Operator order:** run each Orchard script separately, with one login shell and no tty. Run the local builders and mint script on trinity-1-3. Stop on any failed check or uncertain submission; reconcile it before proceeding.

```bash
cd /scratch/jjyeung/orch_n30/r1_ops/work/drv
OSSH=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh
PY=/scratch/jjyeung/envs/p1cpu/bin/python
```

| Order | Exact command | Expected output and required check |
|---|---|---|
| 0, local | `sha256sum -c DRIVER_SHA256SUMS.txt` | Every listed driver, builder, pin record, runbook and validation log reports `OK`. |
| 1 | `timeout 300 bash "$OSSH" 'bash -s' < u1.sh` | `PASS outer SHA; 31 members; sums.txt exact inventory; files 0600`. Bundle must be fresh, 0700. |
| 2 | `timeout 300 bash "$OSSH" 'bash -s' < q1.sh` | `PASS native receipt reused; ordered indices checked; projection 5cf172c4…`. The helper also prints selected/removed counts. |
| 3a, local | `"$PY" -B review_build.py` | `READY rv1.sh; three-review chain pinned; final verdict GO`. Pins all three named verdicts. The first two retain GO AFTER FIXES; review_r1p3 must name the full final archive SHA or config identity and say GO, or GO AFTER FIXES with only explicit LOW non-blocking fixes. The latter prints each fix for the operator. An absent or invalid final verdict produces `PENDING` without creating or changing the install script; stop on that result. Identical existing `rv1.sh` is verified; different bytes are refused. |
| 3b | `timeout 300 bash "$OSSH" 'bash -s' < rv1.sh` | `PASS installed three-review chain; final review_r1p3 accepted for exact packet; no production GO granted`. Installs private `r1.txt`, `r2.txt`, `r3.txt`, and their bound `r1.json`. |
| 4 | `timeout 300 bash "$OSSH" 'bash -s' < ev1.sh` | `STARTED e0; pid …`. Runs once under nohup, nice 19, ionice class 3; reads v7 bytes in the background. |
| 5, at most once/minute | `timeout 300 bash "$OSSH" 'bash -s' < evp1.sh` | Wait for `e0 rc=0` and `PASS four evidence records; staging missing=0; durable archive read-back verified; production_go_granted=false`. A missing rc with a dead process is a failure, not permission to retry. |
| 6 | `timeout 300 bash "$OSSH" 'bash -s' < dv1.sh` | `STARTED d0; pid …`. The worker requires the final archive’s exact `d.py` SHA before reading H or creating KH; a mismatch fails with `REFUSED: d.py SHA differs from final archive`. |
| 7, at most once/minute | `timeout 300 bash "$OSSH" 'bash -s' < dvp1.sh` | Require `d0 rc=0`, printed `compare.json` with `status=READY`, correct config/source manifest, and `missing_source_members=[]`. READY permits the CPU proof; it does not grant production GO. |
| 8 | `timeout 300 bash "$OSSH" 'bash -s' < scan1.sh > scan1.out` | Lists BUN/KH names, archive member names, anticipated proof/session names, submission argv, command lines and all 20 export destinations. Separates inherited names/locators and grep hits. Check every new hit; obtain an independent complete content scan of the final bytes. The listing itself is not a CLEAN certificate. |
| 9a, local | `"$PY" -B cert_build.py ANON_OK.json` | Reviewer-supplied `ANON_OK.json` must be in this work directory, CLEAN with zero unaccepted hits, reviewer, scan SHA, final manifest SHA, and nonempty external file pins. Generates `sc1.sh`; does not invent a certificate. |
| 9b | `timeout 300 bash "$OSSH" 'bash -s' < sc1.sh` | `PASS independent CLEAN certificate installed for final manifest; no production GO`. Verifies external bytes and the inherited full kit inventory. |
| 10, local on trinity-1-3 | `bash L1_mint.sh` | `PASS 20 fresh create-only sessions; mode 0600; URI contents withheld`. Requires the same authenticated gcloud setup and helper as H1. Never reuse H1 sessions. |
| 11a, local | `"$PY" -B session_build.py` | `READY si1.sh mode 0600; contains secret capabilities; never display`. Generates the private install script from `sess_26cc98b7.json`. |
| 11b | `timeout 300 bash "$OSSH" 'bash -s' < si1.sh` | `PASS installed sess.json mode 0600; 20 fresh destinations; contents withheld`. Requires an absent `KH/sess.json`; verifies exact keys and read-back SHA. |
| 12 | `timeout 300 bash "$OSSH" 'bash -s' < pr1.sh` | Prints the user's queue, validates the kit/certificate/sessions, runs `p.py`, prints the full CPU sbatch line, and prints `SUBMITTED job_id=…`. Refuses any pending `a15_cot_ap*` job on advanced or this job name in any partition/state. |
| 13, at most once/minute | `timeout 300 bash "$OSSH" 'bash -s' < pm1.sh` | Prints squeue, bounded tails of `<job>.err`, `.steps`, `.w.steps`, and the proof JSON when present. `NOT_YET` and a proof `RUNNING` status are not PASS. |

`u1.sh` contains the verified archive as a base64 heredoc, so the whole script and payload travel over the single authorized stdin call. Its transport is about 16.5 MB. Binary tar bytes cannot follow shell source on the same stdin without framing. The script creates the fresh bundle, decodes once into private `p.tar`, validates the outer SHA, checks the 31 regular-file members and exact sums inventory, and extracts with exclusive writes. `u3.sh` is the standalone verification/extraction body retained for inspection; the normal order does not call it separately.

`ev1.sh` derives its records from the actual H1 bundle and confirms those records equal H's manifest-pinned copies. Its embedded staging checker is byte-for-byte H1 `payload/v.py`, invoked by H1 `payload/r.py stage`. It checks inherited part availability and hashes every changed staging entry, including v7, against the new projected staging plan. This claim covers read-only verification; upload, extraction and derivation writes are excluded. The archive attestation covers `BUN/t.tar` in project storage, its read-back SHA, its 799 member hashes and the new tree digest. `4.json` inherits the resource envelope and expiry, allows only mode p with zero new GPUs, retains gpu_cap=4/max_parallel_jobs=1, and keeps production GO false. H1's source-specific written approvals and admission evidence are not reused as R1 authority.

`scan1.sh` is a name/argv inventory for the independent content reviewer. Inherited names inside 0700 trees are listed separately under the user's ruling. A reviewer must also inspect final file contents and the proof's generated shell body. `ANON_OK.json` must bind the final `KH/SHA256SUMS.txt`; it must account for inherited names explicitly. Do not treat grep output as the complete content scan or certify the kit from these local tests.

`L1_mint.sh` invokes exactly the H1 helper `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py` with namespace `8865619b`, fresh run `26cc98b7` and slots `m100 m200 mstop mstopB mstopC` (four parts each). This helper was identified from H1's working L1 script; it was not executed or separately audited here. Its output goes to a private local log, never stdout. Do not display `sess_26cc98b7.json`, `si1.sh`, or `mint.private.log`. Minting and live gcloud authentication remain operator checks.

`pr1.sh` serializes this driver's submissions with flock, records a submission-attempt marker before sbatch, and refuses a second attempt. If the login times out around sbatch, inspect the queue and `BUN/sbatch.out` before any further action. A missing `job.id` does not establish that sbatch failed. This local lock cannot serialize other operators; coordinate advanced submissions. No script deletes files, retries failed work, changes H1, or submits the GPU wrapper.

The CPU submission line is:

```bash
PARTITION=advanced
python3 -B "$BUN/p.py" --kit "$KH" --bundle "$BUN" \
  --binding "$BUN/BINDING.json" --partition "$PARTITION" --out "$BUN/a.json"
TZ=UTC env -u TK_JOB_START CUDA_VISIBLE_DEVICES= sbatch --parsable \
  -J a15_cot_ap26cc98b7 -A mt01 -p "$PARTITION" -N1 --ntasks=1 \
  -c 48 --mem=800G -t 04:00:00 --no-requeue \
  -o "$KH/o/%j.out" -e "$KH/o/%j.err" "$BUN/p_26cc98b7.sh" "$BUN/a.json"
```

After the proof finishes, require PASS for `disk_plan`, `routing_selection`, `empty_root`, `temporary_paths`, `runtime_binaries`, `directory_modes`, `loader_audit`, and `required_families`; verify the final identity, manifest, requested/actual advanced partition, node, zero GPU allocation, loader audit and five traces per populated family. The result remains separate from production GO. The proof poll never launches `s.sh`.

Local validation is recorded in `test_results_final.txt`, `builder_results_final.txt`, `guard_results_final.txt`, and `syntax_results_final.txt`. The tests verify upload framing and both hash layers; final native projection using genuine H1 receipt/index bytes relocated locally; rejection of a report in place of a receipt and of an altered index; and the inherited staging checker on small inputs. The sealed `d.py --evidence` reaches READY with production-form records, no Slurm identity, no allocation-time verifier or persistent initialization, and no writes outside the test directory. All four wrong evidence identities fail. The driver refuses altered `d.py` even under `-OO`.

The review tests accept the three-review chain, retain each antecedent verdict, print explicit LOW non-blocking fixes, and reject missing, stale, negative, ambiguous, blocking or above-LOW final conditions. Session tests use fake capabilities and verify exact destinations, mode 0600, secret-free output and overwrite refusal. Queue tests use local Slurm stubs and verify pending-job and repeat-submission refusals. Certificate tests check the builder’s final-kit target and syntax; they do not supply a real certificate.

Two absent H1 fixture archive members contain labeled sentinel bytes in a separate test source. These bounded fixtures test control flow and evidence validation; they do not authenticate production inputs. The tests use `fixture_final`, extracted from the verified frozen archive. Full Orchard staging, content certification, authenticated sessions, the actual allocation and production CPU proof remain operator steps.
