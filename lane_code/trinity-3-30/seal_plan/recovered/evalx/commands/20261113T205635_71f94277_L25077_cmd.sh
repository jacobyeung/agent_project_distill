<!-- recovered by seal_plan: transcript=71f94277 line=25077 utc=2026-11-13T20:56:35.696Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_launcher_verdict_accept_after_fixes.md <<'EOF'
# ORCH: launcher verdict is ACCEPT AFTER FIXES; two fixes before the rehearsal, then I confirm the diff myself

Verdict: `/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_LAUNCHER.md` (27 lines; read it in full). Pins match (packet be05cd4a, digest 45fc2217; `chain_save.py` equals the accepted direct pin). 23 launcher and return tests pass; the reviewer's two finding tests are in `/scratch/jjyeung/orch_cd/leg_s1_review/work_orchard_launcher/copy/test_review_findings.py` (adopt them).

## Fix before the rehearsal (each with a test), as one small diff on the frozen files

1. **F1 (high; `orchard_launcher.py:322`, `:95`):** the submission passes `-` as the script name, but `sbatch` reads the script from standard input only when no file name is given. The call would most likely fail ("Unable to open file -"), be recorded as uncertain and spend the intent. Omit the script argument. If you can do it within the same single call, run `sbatch --test-only` on the same input first (it creates no job) and submit only if it accepts.
2. **F2 (high; `orchard_job.py:72-76`):** the job matches `SLURM_JOB_GPUS` (the node's global index) against nvidia-smi's index, but Orchard constrains devices, so the one visible card is index 0 and the job would refuse at its first card check unless it happened to get GPU 0. Select the row when exactly one card is listed; otherwise match `CUDA_VISIBLE_DEVICES`.
3. **F3 (medium; `orchard_stage.py:220-221`):** `gcloud` writes its token cache and update and usage stamps into `/project/community/jjyeung/gcloud`. Set the variables that disable the update check and usage reporting for the job's calls. Do it in the same diff; it is two lines.
4. **Staging throttle:** apply your prepared one-line change (drop the 8 MB/s limit on copies inside Orchard). That limit is a Trinity rule and adds about 22 minutes for nothing.
5. **Result cap:** an archive over the cap returns INCOMPLETE with no results, which would cost a GPU hour and the decision's timing. Raise the per-read cap to **256 MiB** and the total to **1 GiB** under `/home/jjyeung/okit/evalx_results/` (this replaces the 64 MiB and 512 MiB of my 1848Z answer), and have the job put the archive's size in its exit receipt whether or not it fits.

The low items L1 to L4 wait until after the step-100 read.

## Then

Re-pin, post a RESULT with the new digest and the diff file. I confirm the diff myself (a diff read and your tests, as for the hardware parser) and write the receipt; that takes minutes. On my word the step-50 rehearsal goes, once. The reviewer's list of what the rehearsal must record is in the verdict; above all the compressed archive's size, the `sbatch` answer, the GPU and mount readings, what `gcloud` writes, and per-phase times.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: LAUNCHER REVIEW (Claude Opus high; leg_s1_review/REVIEW_VERDICT_ORCHARD_LAUNCHER.md): ACCEPT AFTER FIXES; pins match; chain_save.py equals the accepted pin. F1 HIGH: sbatch given '-' as script name (reads stdin only without a name) -> submit would fail and spend the intent; F2 HIGH: SLURM_JOB_GPUS global index matched against nvidia-smi's constrained index 0 -> job refuses unless it gets GPU 0; F3 MEDIUM: gcloud writes token cache/update stamps into the project config dir; staging throttle adds ~22 min for nothing; an archive over 64 MiB would return INCOMPLETE with no results. Estimate 1-1.5 h wall. Sent to evalx ($N): fix F1-F3, drop the throttle, cap raised to 256 MiB per read / 1 GiB total; I confirm the diff myself, then the step-50 rehearsal goes once." >> $C/ORCH_HANDOFF.md; echo done $N