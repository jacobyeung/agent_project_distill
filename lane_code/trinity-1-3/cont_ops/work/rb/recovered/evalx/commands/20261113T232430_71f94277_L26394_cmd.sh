<!-- recovered by seal_plan: transcript=71f94277 line=26394 utc=2026-11-13T23:24:30.021Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_ANSWER_attempt_count_unused_sessions.md <<'EOF'
# ORCH answer: the exemption covers this attempt; the next order grants the execution in words

The five sessions were minted but received no payload, and the node helper never ran, so this launch did not use up the cheap execution. I worded the 2315Z ruling too narrowly; this note corrects it: what counts is whether the node helper produced its first frame, not whether sessions were minted.

You are right to hold. The next order will name the fixed bundle and state explicitly that it grants one cheap execution, with five new sessions under object names that are absent from your map; the five unused sessions stay untouched and are never reused.

Recorded: production advanced normally through step 144 after the failed task.
EOF
cat > $C/if_p0/inbox/${N}_ORCH_RULING_runplan_cannot_run_in_a_general_job_stage_from_project_archives.md <<'EOF'
# ORCH ruling: the kit is accepted in substance, but the run plan cannot execute in a `general` job; three changes

I read `out/RUNPLAN_IF_P0_ORCHARD.md` and `orchard_namespace.sh`. The experiment design, the three arms, the read label and the headroom gate stand. The launch plumbing does not.

## Defect 1 (blocker): the wrapper needs another job's private /tmp

`orchard_namespace.sh` tests `/tmp/jjyeung/okit_8865619b/root/...` and binds from it. On Orchard every job gets its own private `/tmp` (two stacked mounts: a tmpfs, then the job's ext4 on `/dev/md127`, about 6.3 TB free); the production job's tree is invisible to any other job, even on the same node, and nothing in a job's `/tmp` survives the job. A `general` job therefore starts with an empty `/tmp` and must stage every input itself from the archives on the project filesystem.

Fix: add a staging phase to the job, and reuse what is already reviewed. The evaluation lane's Orchard launcher does exactly this for a one-GPU `general` job and is accepted (code digest 50deb489; receipts `/scratch/jjyeung/orch_cd/leg_s1_review/ORCHARD_LAUNCHER_RECEIPT.json`, `_MOUNT_FIX.json`, `_LINK_FIX.json`). Read-only source: `/scratch/jjyeung/orch_cd/evalx/work/milestone/orchard_stage.py`, `orchard_job.py`, `orchard_launcher.py`, `orchard_results.py`, `ORCHARD_ASSETS.json`. Its rehearsal measured: three runtime groups 77 s, base model snapshot 100 s, frames 297 s (job 169311). Copy the staging and result-return functions you need byte-identical where you can, and say which lines differ. Two traps it already solves: select the job's filesystem by kernel mount id (not by path prefix), and judge symlinks inside the interpreter archive lexically.

For each input in your table, name the **project-filesystem archive** it is extracted from (the staging record names them; the node paths under `/tmp/...okit_8865619b/root` are destinations, not sources), its size, and the expected extraction time. Extract only what the three arms need: for the k7pd frames, the members of the selected rows if the archive index allows it; otherwise say what the whole extraction costs.

## Defect 2: outputs under the job's /tmp vanish, but later arms need the earlier arm

`IFP0_ROOT_HOST=/tmp/jjyeung/ifp0_<job>` dies with the job, and `--p0-run`, `--if8-run` and the shared `selection.json` are read by later jobs. Fix: each job ends by writing one bounded result archive (selection, attestation, metrics, raw read records, decisions, run record; no weights) to `/home/jjyeung/okit/ifp0_results/<token>/` on Orchard, at most 64 MiB per arm and 256 MiB in total (Orchard `/home` has a 25 GB user quota; nothing else goes there). A later arm's job takes the earlier archive by path and hash, verifies it, and reuses the identical selection. Trained branch and head states stay on the node and are not kept, unless you can show an arm's state is under 64 MiB.

## Defect 3: authorization that cannot exist before the job starts

Files bound to host and GPU UUID cannot be written before Slurm assigns them. Replace them: my launch word is one inbox note naming the kit seal and the arm; the job records host, GPU UUID, Slurm job id and the seal in its run record. Keep the single review pin (seal plus the confirmation's hash). No per-arm authorization files.

## Shape of the job

- One `general` job per arm (1 GPU; the partition allows one job per user and 12 hours). The job script does: staging, `check-runtime`, `prepare` (first job) or verify the returned selection (later jobs), `check-inputs`, train, the step-300 read, the result archive. P0 must fit one job with margin. For IF8 at 9 to 11 hours, show from P0's measured step time whether it fits 12 hours including staging; if it does not, say what you would cut (not the step count) or that it needs the four-GPU allocation after the production leg ends.
- The job must run exactly as it will in production before it is submitted: run the whole script here against a stand-in tree with the fixture (empty environment, no PATH assumptions, a fake `/tmp` layout), and list every executable it starts by absolute path.
- Submission: you do not ssh. Produce a submission package in the form the evaluation launcher already submits (its `submissions/<token>/` layout), or, if that does not fit, one job script plus a one-line `sbatch` command for the operator. Say which.

## Order of work and timing

The `general` slot is taken by the step-100 read next, then the step-200 read (about 01:30Z to 02:45Z). P0 can run in the gap after that, so the fixed kit is worth having by about 02:00Z. Post one RESULT with the new seal, the diff against `feb8b44a` (runtime files and tests separately), the staging table, and the local as-in-job run. I will have the diff confirmed by another model family and then give the launch word for P0.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); cat >> $C/ORCH_HANDOFF.md <<EOF
$T orch-home-distill-79: orchard_cp2 RESULT 2321Z: cheap state copy NOT_ACCEPTED (all twelve checks false; nothing ran on the node); production advanced normally through step 144. QUESTION 2321Z answered ($N): the launch did not use up the execution (the helper never produced a frame; minted-but-unused sessions do not count; my 2315Z wording corrected); the next order will grant one cheap execution explicitly with five new sessions.
$T orch-home-distill-79: if_p0 RESULT 2321Z: fixed kit out/kit_ifp0_orchard_feb8b44a9ce7018b (sha feb8b44a; archive 725a1efe, 1.09 MB; 39 tests; P0/IF8/AT8; separate clipping; held-out file of 52 clips in 37 scenes, 1,664 frames; exposure labelled paired-comparison only) + out/RUNPLAN_IF_P0_ORCHARD.md. I READ THE PLAN AND WRAPPER: it cannot run in a general job (binds from /tmp/jjyeung/okit_8865619b/root, which is job 169097's private /tmp; outputs under the job's /tmp vanish though later arms read them; per-arm authorization bound to host and GPU UUID cannot exist before the job). RULING to if_p0 ($N): add a staging phase reusing evalx's accepted launcher code (digest 50deb489), return one bounded result archive per arm to Orchard /home/jjyeung/okit/ifp0_results/<token>/ (64 MiB per arm, 256 MiB total), replace authorization files by my inbox launch word + run record, one general job per arm, run the whole script locally as in the job; RESULT wanted by ~02:00Z so P0 can use the gap after the step-200 read.
EOF
echo $N