# REVIEW_VERDICT_CONTINUATION_CARD

**Verdict: NO-GO for the card as written.**

The continuation path has substantial byte-integrity checks and preserves slot A under the listed, single-job conditions. However, the command does not unconditionally select A/544, rule E cannot establish semantic restore equality, and several full-filesystem failure paths contradict the card. The supplied packet still marks restore equality and the verified stop procedure as missing.

I reviewed local evidence only. I made no SSH connection, submission, intervention, or file change. Checker experiments used in-memory inputs.

**(a) Filesystem and resume behavior, derived before reading the card**

| Data or operation | Physical destination | Evidence |
|---|---|---|
| Restored checkpoint, binding and inputs | Node-local `/tmp/jjyeung/okit_8865619b/runs/469ddece` | [wrapper:15](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:15), restore at lines 27–56 |
| Staging, environment, model/data copies, writable kit and caches | `/tmp/jjyeung/okit_8865619b/...` | [c.sh:18](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:18), lines 265–378 |
| Trainer checkpoints, metrics, attempt reports and milestone weights | The logical code-aws run path is bind-mounted onto that node-local run directory | [c.sh:345](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:345) |
| Wrapper/kit logs, GPU samples, upload logs and receipts | Shared NFS `/project/community/jjyeung/okh7/x_07ca49df/...` | Resolved paths in [inv1.out:3](/scratch/jjyeung/orch_n30/cont_ops/work/inv1.out:3); writers in [r.sh:69](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_b_r.sh:69) |
| Mirrored JSON/JSONL and admission reports | Project filesystem, copied periodically and at normal shell closeout; checkpoint directories and weight payloads are excluded | [c.sh:398](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:398) |
| Export tar files | Node-local `.../up/`; uploaded to GCS using project-resident session and receipt files | [c.sh:404](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:404) |
| Persistent continuation state | Project filesystem: `/project/community/jjyeung/okh7/r/5da50f2b/{A,B}.*` | [inv1.out:6](/scratch/jjyeung/orch_n30/cont_ops/work/inv1.out:6), [wrapper:79](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:79) |

The wrapper selects the highest recorded verified slot. If the node-local run has no `checkpoint_*/complete.json`, it extracts that slot, checks its archive hash, manifest hash, step, binding and inputs directory, then starts `job.sh`. The job verifies the kit, selects resume mode, runs mode-p admission, and launches four ranks. After the child exits, the wrapper attempts to publish the latest complete checkpoint into the other slot. [wrapper:18](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:18), [job.sh:14](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_job.sh:14), [r.sh:24](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_b_r.sh:24)

Two corrections follow:

- The card contradicts itself about `/home`: line 11 says the job never reads it; line 46 acknowledges pinned staging inputs there. The source and staging inventory support those reads. The supplied `df` shows `/home` at 83%; the quota command returned `rc=1`, which does not establish that the user is over quota. [card:11](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:11), [card:46](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:46), [inv1.out:288](/scratch/jjyeung/orch_n30/cont_ops/work/inv1.out:288), [inv2.out:148](/scratch/jjyeung/orch_n30/cont_ops/work/inv2.out:148)
- “Keeps the two newest” understates local storage. Older checkpoints are moved into `_superseded`, retaining their payloads. Only two remain in the active checkpoint namespace. [card:27](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:27), [trainer:1906](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:1906)

**(b) Run identity, cold-start protection and slot A**

**Supported under the listed state:** A is the sole verified slot, at step 544, with matching recorded archive digest and a 112,988,477,440-byte archive. `RUN.json` identifies run 469ddece and first job 169097. The locally recomputed wrapper, job, `r.sh` and `c.sh` hashes match the Orchard listing. [inv1.out:44](/scratch/jjyeung/orch_n30/cont_ops/work/inv1.out:44), [inv1.out:112](/scratch/jjyeung/orch_n30/cont_ops/work/inv1.out:112)

**Cold fallback is blocked.** The selector rejects missing/invalid retained checkpoints, cold mode with previous-job or slot history, foreign binding, and a maximum restored step older than the newest slot. The trainer receives `resume_pin="latest"` and raises if no complete matching state exists. [r8.py:96](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_r8.py:96), [r8.py:132](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_r8.py:132), [w.py:177](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_w.py:177), [trainer:1814](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:1814)

**Blocking finding: the command does not pin A/544 exactly.**

1. Any existing local `complete.json` suppresses archive restoration.
2. The selector checks the **maximum step** among verified local checkpoints and permits steps greater than 544.
3. The trainer selects `latest` by **manifest modification time first**, then step.

Thus a retained newer checkpoint can replace A/544 as the source. With multiple local checkpoints, an older checkpoint with a newer modification time can also be selected even though the selector accepted the maximum step. The supplied listings do not inventory the eventual compute node’s run directory. [wrapper:27](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:27), [r8.py:128](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_r8.py:128), [trainer:1767](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:1767), [trainer:1830](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:1830)

**Required correction:** establish a pre-update check that the actual selected resume manifest is the recorded A/544 manifest, including its digest. Checking the first metrics row catches a mismatch only after an update.

**A preservation passes conditionally.** With unchanged records and one continuation, A remains the newest verified slot, so the wrapper targets B. It verifies B’s temporary archive before publication. Restore failures exit before closeout. This protects A independently of rule E. It is not a cross-job locking guarantee. [wrapper:37](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:37), [wrapper:76](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:76), [wrapper:164](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:164)

The wrapper can publish B after a nonzero trainer exit: it records `rc`, then performs checkpoint publication without requiring `rc == 0`. A published B therefore does not prove semantic acceptance or a rule-E pass. [wrapper:66](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:66)

**(c) `/dev/null`, project stderr and `TK_JOB_START`**

**No supplied core control path parses the batch stdout file.**

- The stall guard watches run-file sizes and modification times.
- Rule E reads metrics JSONL.
- Signal relays inspect processes and send signals.
- Upload bookkeeping reads receipts and `.done`/`.claim` files.
- Closeout selects checkpoint manifests.

Consequently, discarding batch stdout does not remove an input used by those mechanisms. Upload stdout/stderr are separately redirected into `gcs.log`. The evidence does not include a complete new-job external monitor implementation, so it cannot establish that every external consumer is compatible. [sg.py:11](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_sg.py:11), [early_loss_check.py:7](/scratch/jjyeung/orch_n30/cont_ops/work/early_loss_check.py:7), [h.py:7](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_h.py:7), [c.sh:429](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:429), [GATES.json:95](/scratch/jjyeung/orch_n30/cont_ops/work/packet/GATES.json:95)

**Blocking finding: “stderr … no crash path” is false.**

The stall guard executes an unguarded, flushed stderr print **before** relaying its stop request. A failed write can prevent the relay and termination sequence. Separately, `r.sh` appends the project-resident stop flag under `set -e` **before** forwarding USR1; that failure can abort the handler. `/dev/null` does not protect either path. [card:36](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:36), [sg.py:79](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_sg.py:79), [r.sh:3](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_b_r.sh:3), [r.sh:13](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_b_r.sh:13)

**The upload failure description is incomplete.**

- If opening `gcs.log` fails, the uploader is skipped.
- If an existing log opens but a later write fails, uploads may already have occurred.
- Receipt appends are unguarded. A failed or partial receipt can leave remote objects without reliable bookkeeping; malformed receipt JSON also breaks subsequent reads.
- `.claim` and `.done` writes are unguarded under `set -e`. Their failure can terminate the background persister or the foreground closeout.

“Retries every 600 seconds” therefore holds only while the persister survives. Its cadence also includes time spent copying and uploading. [c.sh:423](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:423), [gcsput.py:57](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_gcsput.py:57), [gcsput.py:104](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_gcsput.py:104), [r.sh:69](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_b_r.sh:69)

**`env -u TK_JOB_START` is safe and redundant for this wrapper.** The wrapper unconditionally sets a fresh timestamp before restore. `job.sh` and `r.sh` preserve it, and the trainer charges elapsed restore/staging/admission time against the allocation budget. It does not reset the training step or LR schedule. [wrapper:14](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:14), [job.sh:12](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_job.sh:12), [trainer:2723](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:2723)

**(d) Rule E**

**The thresholds are fixed, and their arithmetic reproduces.** Recomputing medians and MADs from rows 530–544 gives the constants embedded in the checker. They are fixed before this proposed launch. The inventory script captured rounded four-rank means; it did not authenticate the complete metrics prefix or validate every rank while extracting that baseline. [early_loss_check.py:4](/scratch/jjyeung/orch_n30/cont_ops/work/early_loss_check.py:4), [BASELINE_ROWS_520_544.json:112](/scratch/jjyeung/orch_n30/cont_ops/work/BASELINE_ROWS_520_544.json:112), [inv3.sh:16](/scratch/jjyeung/orch_n30/cont_ops/work/inv3.sh:16)

| Failure | What rule E establishes |
|---|---|
| Supplied parent cold start | Caught. After relabeling its first three rows as 545–547, medians were pose **0.26408**, VQA **0.20643**, routing **1.12878**: all alarm. Pointing **0.52323** passes. |
| Wrong LR position | Not reliably caught. The checker reads no LR. The trainer computes LR from the global step, but loss agreement does not verify that computation. |
| Replayed data | Incorrect low step labels can alarm. Replayed rows with correct new labels can pass; the checker examines no sample IDs or sampler-plan digest. |
| Lost optimizer state | Not reliably caught. The checker examines no optimizer moments or step counters. Small early loss changes can remain inside its wide bands. |
| Wrong RNG state | Not reliably caught. No RNG-state comparison exists in the checker. |

The trainer’s LR and sampler code supports the intended continuation, but this is separate from rule E’s detection power. [trainer:1563](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:1563), [trainer:2243](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:2243), [early_loss_check.py:24](/scratch/jjyeung/orch_n30/cont_ops/work/early_loss_check.py:24)

**Blocking implementation defects, reproduced in memory:**

| Input | Actual result |
|---|---|
| Steps 548, 549, 550 | `PENDING`, because all rows are discarded |
| Steps 545, 547, 548 | `PENDING`, despite the gap and later progress |
| Duplicate 545 followed by 546, 547 | `PASS`; dictionary assignment hides duplication |
| Rows ordered 547, 545, 546 | `PASS`; sorting hides order |
| Missing top-level step | Unhandled `KeyError`, not a verdict |
| Valid row followed by an incomplete JSON tail | `ALARM` |
| Baseline steps 530–532 relabeled 545–547 | `PASS` |

These behaviors come from filtering before sequence validation and storing rows by step. A partial live capture can therefore cause a false alarm, while missing expected steps can remain pending indefinitely. The tool also returns normal process success for printed `ALARM`; callers must parse the verdict. [early_loss_check.py:9](/scratch/jjyeung/orch_n30/cont_ops/work/early_loss_check.py:9), [early_loss_check.py:31](/scratch/jjyeung/orch_n30/cont_ops/work/early_loss_check.py:31)

**False-alarm estimate:** the thresholds are broad relative to the observed fluctuations.

| Stream | Baseline MAD | SD over steps 520–544 | Largest adjacent change | Alarm half-width |
|---|---:|---:|---:|---:|
| Pose | 0.00920 | 0.01322 | 0.04267 | 0.08358 |
| VQA | 0.00734 | 0.00848 | 0.02542 | 0.06529 |
| Routing | 0.00275 | 0.00605 | 0.02000 | 0.02446 |
| Pointing | 0.02317 | 0.04532 | 0.16679 | 0.25543 |

All **23 overlapping three-step windows** in the supplied 25 rows pass. That suggests a low loss-only false-alarm risk under similar conditions, but it does not calibrate a production rate. The windows overlap, the calibration rows are reused, and routing is visibly skewed. [baseline rows:1](/scratch/jjyeung/orch_n30/cont_ops/work/BASELINE_ROWS_520_544.json:1)

For scale only: independent Gaussian losses with the MAD-derived standard deviation would give a combined median-of-three tail probability around \(10^{-17}\). Using the observed standard deviations instead gives roughly \(4\times10^{-9}\), dominated by routing. Neither is a defensible operational guarantee. Even zero alarms in eight independent windows would leave a roughly 31% one-sided 95% upper bound.

**Required correction:** retain E as a secondary gross-loss alarm. Fix sequence/schema handling, bind it to the new attempt and selected checkpoint, and define stale/no-progress handling. Do not use an E pass as proof of restore equality. The supplied contract explicitly prohibits that substitution. [GATES.json:40](/scratch/jjyeung/orch_n30/cont_ops/work/packet/GATES.json:40), [canary_contract.json:1](/scratch/jjyeung/orch_n30/cont_ops/work/packet/canary_contract.json:1)

**Observation delay is understated.** A 600-second persistence interval plus a five-minute watcher permits roughly 900 seconds, or about seven updates at 131 seconds/update, before detection—plus copy/upload time. If project persistence fails, there is no finite bound. “Up to about five” is not established. [card:74](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:74), [card:113](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:113)

**(e) Time budget and loss exposure**

The measured mean over steps 530–544 is **131.1169 seconds**. Thus:

\[
456 \times 131.1169 = 59{,}789.3\text{ seconds}
= 16\text{ h }36\text{ min }29\text{ s}.
\]

Those values are rank-0 step timings, excluding separately recorded checkpoint/export durations. [inv3.out:79](/scratch/jjyeung/orch_n30/cont_ops/work/inv3.out:79)

| Component | Reasonable arithmetic allowance |
|---|---:|
| 456 steady-rate updates | 16:36:29 |
| First save + approximately eight periodic saves + final save | About 12:46 at 76.6 seconds/save |
| Three exports | 12:00 using the card’s allowance |
| Staging/admission/model startup to attempt | 2:06:49 from the previous allocation |
| Extra first-update cost | About 4:53 using the previous cold update |
| Archive restore | 8–12 minutes, unmeasured |
| End-slot write and verification | 15:08 measured |
| **Subtotal** | **About 19:36–19:40** |

The card counts eight saves without separately allowing for the mandatory first resumed save and final save. The source requires both. [trainer:2285](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:2285), [trainer:2300](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:2300), [CPU_PROOF.json:254](/scratch/jjyeung/orch_n30/cont_ops/work/packet/CPU_PROOF.json:254)

That subtotal still excludes unmeasured restore overhead. The control flow invokes checkpoint hashing through `g.py`/`r8.py` four times before training, followed by native state loading. Archive verification throughput is not a measurement of extraction, local rehashing and optimizer deserialization. The packet’s more conservative scenario totals **20:25:02**, explicitly without a completion guarantee. [job.sh:16](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_job.sh:16), [r.sh:24](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_b_r.sh:24), [g.py:36](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_g.py:36), [CPU_PROOF.json:269](/scratch/jjyeung/orch_n30/cont_ops/work/packet/CPU_PROOF.json:269)

**The budget guard anticipates costs; it does not simply stop at 23:00.** With configured allowances of 300 seconds/step, 600/checkpoint and 600/export, it can request stopping around **22:15–22:35 elapsed**, depending on pending save/export work. Saves, uploads and slot publication then consume remaining time. [trainer:2289](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_native_loss_producer.py:2289), [config:1](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_k_b02e4385.json:1)

**Assessment:** step 1000 plausibly fits. The evidence supports a conditional estimate around 20 hours, not a guaranteed three-hour operating margin. At 226 seconds/update, updates alone require **28:37:36**, so that rate cannot finish.

If project storage fills:

- **At a milestone:** weights remain local, but upload or its bookkeeping may fail. Earlier verified remote exports survive. No milestone alone guarantees a persistent optimizer checkpoint. [c.sh:405](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:405), [CPU_PROOF.json:107](/scratch/jjyeung/orch_n30/cont_ops/work/packet/CPU_PROOF.json:107)
- **At closeout:** B is skipped when free space is below checkpoint+inputs+binding size plus 20 GB—approximately **133 GB** using A as reference. A remains usable. Mid-copy failure can leave `.part` files. [wrapper:80](/scratch/jjyeung/orch_n30/cont_ops/work/packet/source_jl13.sh:80)
- **If neither B nor the latest export becomes durable:** exact continuation progress since 544 is unavailable after node-local storage disappears. A remote weight export supports a warm start, not recovery of optimizer/RNG state.
- **Reaching step 1000 does not imply m1000 reached GCS.** The card’s unconditional statement at line 49 is contradicted by its own upload failure case. “Exports are kept” must mean successfully uploaded exports, not every local export. [card:49](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:49), [c.sh:429](/scratch/jjyeung/orch_n30/cont_ops/work/kitsrc/b_c.sh:429)

The proposed 50 GB launch-space check neither assures eventual B publication nor reserves working space for logs and receipts. [card:110](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:110)

**(f) Remaining unsupported or overstated card claims**

The findings above cover the substantive source contradictions. These additional claims lack the stated evidence or require qualification:

| Card location | Evidence gap |
|---|---|
| [Lines 3, 18](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:3) | `inv5.out` is absent. The second test-only result, job 169980 and 22:59:04 estimate are not supplied. `inv5.sh` contains a command, not its execution result; its stderr path uses the `/home` alias rather than the literal section-3 path. The retained result is 169979 at 22:47:05. |
| [Line 11](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:11) | “Ready” conflicts with the packet’s missing real CPU equality, baseline-readiness and verified-stop gates. No disposition superseding those gates appears in the reviewed evidence. |
| [Lines 19, 24](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:19) | Wrapper/job hashes are freshly supported; a fresh complete 95-file inventory and a search of every installed kit file for `SLURM_JOB_NAME` are not. In-job inventory verification is future enforcement. |
| [Lines 25, 58](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:25) | “Verified today” is metadata agreement, not a fresh archive payload rehash or native restoration. The historical publication record is present; actual restored-byte validation remains future work. |
| [Lines 26, 43](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:26) | Four GPUs are requested; the supplied listings do not identify their model as H100. The old compute log reports 5864 GiB free, but does not establish the future node’s free space or its `/tmp` filesystem type. Login-node `df` is not compute-node evidence. |
| [Line 29](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:29) | Session names and file mtime are shown. Session creation times, remaining validity and future successful uploads are not. The card correctly labels expiry as an assumption. |
| [Line 48](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:48) | The precise 215.6 GB at 18:23 and 100–240 GB/hour swing are not demonstrated. Retained samples show 217.344 GB and 215.257 GB free. |
| [Line 59](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:59) | The supplied `CPU_PROOF.json` reports metadata/argument checks, zero optimizer updates and no production restore test. It does not provide the claimed four-rank, three-step, \(10^{-6}\) equality result. |
| [Line 61](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:61) | No cancellation test establishes “stops at once” or “B is not written.” Absence of a TERM trap alone does not prove those outcomes. A stale project metrics mirror also cannot prove that optimization stopped. |
| [Line 64](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:64) | CPU resource requirements are recorded, but the 90-minute production duration is unmeasured. The listings do not show evalx27 occupying `general`; the user’s queue listing contains no such running job. “Bad resume detected in about three hours” exceeds rule E’s demonstrated scope. |
| [Line 76](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:76) | The claimed November 14 ORCH ruling limiting registered milestone stop rules to 100/200 is not established by the supplied runtime evidence. |
| [Lines 80–86](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:80) | Restore duration, steady export cost, future node, queue start and finish are estimates. The supplied evidence does not demonstrate the cited canary’s 226-second rate or guarantee completion. |
| [Lines 7, 90, 93, 97](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:90) | The recipe supports the row mix. The listed evidence does not establish m400/m544 evaluation scores, the grammar ruling, 15.3/95.0/57% violation counts, projected violation totals, or measured drift of untrained types. |
| [Line 91](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:91) | A different node and empty EMA are conditional on placement and the absence of retained local metrics. The slot excludes old metrics, but the wrapper can reuse a local run. A resumed-versus-uninterrupted numerical comparison is absent. |
| [Lines 102–105](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:102) | Held jobs and dependency chains are shown. Main’s agreement, native_r2’s readiness, a cost-free pilot window, evalx27’s placement and alternate-reader readiness are not. Scheduling estimates cannot guarantee “costs nothing.” |
| [Lines 110–113](/scratch/jjyeung/orch_n30/cont_ops/work/review_input/PRELAUNCH_CARD_CONTINUATION.md:110) | These are planned procedures, not completed checks. No supplied new-job observer proves a 450-second step alarm, timely missing-row detection, or operation through failed project persistence. |

Before this card can support GO, it needs an exact pre-update A/544 selection check, resolution of the missing restore-equality gate, a corrected and attempt-bound rule E, a verified stop/observation procedure, and corrected storage and durability claims. These are review requirements; no launch or intervention was authorized or performed.