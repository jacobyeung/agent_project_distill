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
