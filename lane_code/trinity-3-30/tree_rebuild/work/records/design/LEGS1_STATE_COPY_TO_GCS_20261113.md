# LEG-S1: exact-resume state on GCS

## Question
Can a running Orchard job's exact-resume state be copied to GCS from inside the job, as insurance against the shared project filesystem filling?

## Answer and status
The metadata-scale transport works, but a safe full-state copy is not qualified for this kit. The state-copy line is CLOSED for job 169097: no full copy or end-only fallback will run, and the agreed runbook stays unchanged.
Bundle `d93d0359fcb38e00b05dd28f1438433fd76e86c7843f02cfba298ae41cc63dab` implements pinned-handle copying, two archive checks, four ordered uploads, private receipts, a final manifest and detached return transport. <ref_file file="/scratch/jjyeung/orch_cd/leg_s1_canary/out/STATE_COPY_DELIVERY_169097_20261113T2329Z_b9bfe98f.json" />
The 2,724,659,200-byte cheap archive of checkpoint 160 and its five server generations are confirmed. It is NOT_A_RESUMABLE_SLOT. Rates are approximately 434 MB/s for creation, 270 MB/s across two verification passes and 129 MB/s for serial upload.
Nine of twelve checks pass. Allocation memory, trainer membership and unchanged trainer step time remain false; no live full-state restore has been demonstrated. <ref_file file="/scratch/jjyeung/orch_cd/leg_s1_canary/inbox/20261114T004000Z_cp2_d93_cheap_NOT_ACCEPTED.json" />
The full copy fails the memory-scope and timing gates. Its serial stream does not establish the 170 MB/s floor; the conservative three-times window exceeds the 7,200-second save interval. The wrapper also exits on a slot-space refusal, ending the allocation that a fallback needs.
A reviewed warm-start contingency can use a confirmed weight export, but it is not exact resume or launch authority; production loading and GPU steps remain untested. <ref_file file="/scratch/jjyeung/orch_cd/leg_s1_review/CONFIRMATION_WARM_START_d2eb7e3b.json" />
Export confirmation remains necessary: project ENOSPC can prevent the automatic uploader's log/claim path from starting. Do not infer delivery of a future stop export from the contingency's existence. <ref_file file="/scratch/jjyeung/orch_cd/leg_s1_canary/out/FULL_PROJECT_FS_ANALYSIS_169097.md" />

## Facts worth keeping
- Job `/tmp` has stacked tmpfs and ext4 mounts. Select the opened path's kernel mount ID from fdinfo, not the first or longest-prefix mount-table entry; retain the selected entry and all `/tmp` entries. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097_b9bfe98f/transport_decoded.json" />
- Login `/tmp` is a small tmpfs. Use verified local `/var/tmp` for the small control/return spool, not the full archive; the detached 3,072-byte round trip passed on ext4. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/events/20261113T2303Z_RESULT_login_var_tmp_dry_pass.md" />
- `srun --export=NONE` requires absolute executable paths, including `/usr/bin/env`, and an explicit PATH, locale, GPU visibility and private HOME/TMPDIR. Test the launcher in an empty environment. <ref_file file="/scratch/jjyeung/orch_cd/leg_s1_canary/work/state_copy/operator_transport.py" />
- A 120-second access-session ceiling requires a detached launch and a separate fetch. Preserve raw output, nonce, length, hash and exit receipt; a lost return blocks acceptance but does not prove that no remote manifest committed. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097_b9bfe98f/exit.json" />
- The trainer keeps two newest complete states and renames older UUID folders into `_superseded/`. Pinned directory/file handles survive renames; mutations must fail verification. Do not reopen payloads through the old pathname. <ref_snippet file="/scratch/jjyeung/orch_cd/leg_s1_canary/work/source_snapshot_mdg_v2/student_pilot/carrier_c1_run.py" lines="1833-1917" />
- Job memory.current was 716.9 of 800 GiB, including 668.3 GiB file memory, 667.7 GiB inactive file and 27.9 GiB anon. Dirty/writeback and OOM kills were zero; 1,714 cumulative max events do not date a failure. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/events/20261114T0036Z_RESULT_memory_step6_cache_dominates_no_oom_kill.md" />
- The measured overlapping step repeated the 800 GiB limit but accounted for its own usage, not its ancestor's 768 GB. Equal limits do not imply equal process populations or headroom. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/out/STATE_COPY_CHEAP_169097_b9bfe98f/memory_scope_failure.json" />
- The helper used four CPUs, nice 19, idle IO and 512 MiB address space; srun itself had no address-space override. Its 3.8 TB node reserve plus 20 GB margin exceeded the native remaining-reserve floor. These snapshots are not future reservations.

## Time budget
Use the actual final inventory. The planning reference is B = 113,055,593,770 bytes, including a 64 MiB tar allowance, not a measured final archive.
For two verification passes, T = B/R_archive + 2B/R_verify + B/R_upload + 60 seconds. The measured serial projection is 260.8 + 836.2 + 873.4 + 60 = 2,030.4 seconds, or 33.84 minutes.
Halving the rates under the existing ceilings gives 66.68 minutes; three times that is 200.04 minutes. This exceeds both the 120-minute save interval and the helper's 38-minute hard limit.
The final-hour budget leaves 3,600 - 77 - 300 - 69.7 - 900 = 2,253.3 seconds, or 37.555 minutes, after save, packing, one stop export and the 15-minute wall margin. Add every backlog item. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/out/FINAL_HOUR_BUDGET_169097_20261113T234025Z.json" />
Four concurrent parts at the job's 309.8-433.1 MB/s aggregate project 23.63-25.37 minutes with both verifiers. Using 80% of creation/verification rates and 80% of 309.8 MB/s projects 31.46 minutes, leaving 6.10 minutes of work headroom.
The old halving plus 150 MB/s upload ceiling still gives 50.13 minutes even with four parts. Cheap parts were 0.681 GB, exporter parts 5.396 GB and planning full-state parts 28.264 GB; setup and sustained-rate effects remain unbounded. <ref_file file="/scratch/jjyeung/orch_cd/leg_s1_canary/out/STATE_COPY_END_TIMING_169097_b9bfe98f.json" />

## Options rejected for job 169097
- Mid-run full copy cannot satisfy the scope, lone-stream and conservative timing gates, and it would add unproven CPU/cache/IO interference to training.
- End-only serial copy has under four minutes of measured-rate budget headroom and misses the conservative budget. A space refusal exits the wrapper immediately; a sidecar cannot assume the scheduled wall end preserves its allocation. <ref_snippet file="/scratch/jjyeung/orch_cd/orchard_cp2/work/adm/jl13.sh" lines="81-89" />
- Four concurrent parts require new cancellation/deadline, receipt-ordering and memory-reserve logic. They are a next-kit candidate, not an approved modification to this running job.
- One verification pass would require a reviewed combination of both semantic/hash checks. Simply omitting the native validator weakens integrity; the two passes were not timed separately, so halving verification time is not established.
- Orchard `/home` has no verified per-user quota or refreshed compute-node capacity for this copy. The current `okit/r` link resolves to the project filesystem; retargeting live paths is not an approved destination change. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/events/20261113T1833Z_RESULT_home_filesystem_and_root_path.md" />
- Keep-size preallocation is unsupported by the tested login NFSv3 mount; compute-client support is unproved. It does not reserve space for the unchanged wrapper's truncating tee path. <ref_file file="/scratch/jjyeung/orch_cd/orchard_cp2/out/PREALLOCATION_PROBE_169097.json" />

## Requirements for the next kit's seal
- Make full-state GCS persistence native to the trainer's wrapper and the primary end-state destination. Treat the project slot as optional; give durable state priority over optional work.
- The wrapper must retain allocation ownership through the GCS attempt and its terminal receipt. A project-space refusal must not exit before that attempt. Do not retrofit the live wrapper.
- Stage upload controls privately before project failure. Archive creation, logs, receipts and the return path must not require new project writes; send payloads directly between Orchard and GCS, never through Trinity.
- Preserve inputs, binding, model/optimizer state, every rank's RNG and sampler/progress state, authentic run identity and the loss baseline. Verify the native checkpoint predicate, archive content and whole/per-part hashes.
- Upload four ranges concurrently with bounded aggregate CPU/RSS/cache use, per-worker and overall deadlines, unique receipts and cancellation limited to owned workers. A 600-second socket timeout or a main-thread alarm does not bound progressing worker uploads.
- Publish the canonical manifest only after every part's exact size, checksum and server generation verifies. Use fresh names/capabilities; do not automatically retry an ambiguous or interrupted session.
- Authenticate the job scope from trusted job/step identity and launcher/rank PID start times, UID and cgroup membership. Require trainer/launcher/rank exit and no concurrent state or slot writer before end-state persistence.
- Sample every finite enforcing ancestor, not one selected group, with current/stat/events/pressure evidence. Refuse unreadable scope or new OOM evidence; record limit-event deltas rather than treating a cumulative count as a current failure.
- For each ancestor, use R = min(current, max(0, inactive_file - file_dirty - file_writeback - shmem)), P = current - R, and require P plus the admitted copy reserve <= 85% of its limit. This proposed cache-aware policy requires independent review; anon alone is insufficient.
- Reserve for all concurrently resident source/archive pages and workers. The planning serial reserve is 141.8 GB; four cached parts need at least 226.6 GB plus worker allowance. Retain bounded buffers, incremental flush, native disk reserves and the wall margin.
- Seal an explicit end-only timing policy against measured full-size phase rates. Budget approximately 31.46 minutes under the stated four-part projection, then replace that forecast with the canary's result; abort before the 15-minute wall margin.
- Restore from generation-pinned GCS objects into a genuine node-local verified state source. Bind archive/binding/run identity through the standard restore and continuation gates; no fake project slot or unreviewed source-path bypass is acceptable.

## Tests that would settle it
Run an authorized canary with the intended world size, production-scale state, memory limits, concurrency and wrapper lifetime. Measure cold/full-size creation, both verification passes, upload, cache pressure and end-to-end completion.
Have it train, save and upload its full native state to GCS. Confirm the manifest and all generations independently; then have the operator cancel that canary and start a fresh allocation using only the GCS state.
Compare restored model and optimizer tensors, CPU/CUDA RNG, scheduler/absolute step, row/sampler position, binding, run identity and loss baseline. Check the next batch and update against an uninterrupted control under the declared determinism contract.
Inject a full project filesystem, refusal before slot writing, expired/partial/finalized sessions, a lost return, one failed worker, timeout, dirty-cache pressure, an unreadable ancestor, malformed members and source mutation. No incomplete case may publish a success manifest.
Exercise stacked mounts, explicit `/var/tmp` login spooling, empty-environment launch, detached fetch and checkpoint rename fixtures. Prove that a space refusal keeps the allocation alive for the bounded GCS attempt.
Toy CPU fixtures, metadata-only copies and warm starts do not establish exact production resume. Seal and independently review this path before a production leg relies on it; this record authorizes no launch or cancellation.
