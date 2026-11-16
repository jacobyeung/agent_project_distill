<!-- recovered by seal_plan: transcript=71f94277 line=12268 utc=2026-11-12T12:24:32.216Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > leg_s1_tree/inbox/${T}_ORCH_final_verdict_launch_ready.md <<'EOF'
# ORCH: the last review says LAUNCH-READY (code, mix and documents) on seal 38917ea5; three small points, none needs a new source seal
Verdict: /scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_NF.md. Thank you: every fix fails its test on revert, the allowlist is right in both paths, the mix recomputes exactly, the kit binds the new route file.
- N1, my decision: accepted as it stands for this leg. Camera-object absolute distance trains on no rows (its 5,040 older programs are deferred and no direct source exists), as do the VSTI camera-object relative and object-object types, relative count and relative size. Do not change the route file. State it in the card in one paragraph: these types keep the parent's behaviour in this leg; their dev and benchmark reads at m100 and m200 are reported as "untrained in this leg".
- N2, documents: add to the card the consequence above and the route evidence from held-out scenes (/scratch/jjyeung/orch_cd/evalx/events/20261112T1156Z_RESULT_devs1_route_table_predicted_masks.md: absolute distance routes at +8.1 [+0.9, +16.9]; room size is undecided at +6.7 [-14.4, +25.0] and stays routed by the plan's rule; direct wins on the other six types).
- N3 goes to the operator (submit with the inherited job-start variable cleared).
Then post your RESULT with the kit, the card and the packet. The launch waits only for the cluster's storage workaround and my go to the operator.
EOF
cat > orchard_cp2/inbox/${T}_ORCH_review_ready_and_N3.md <<'EOF'
# ORCH: the last review says LAUNCH-READY on the no-flag kit (seal 38917ea5; all 90 kit checksums verify; it binds routes.json 62c54ed4); one operator point for the submit
N3 from /scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_NF.md: job.sh keeps any inherited TK_JOB_START, and sbatch exports the submitter's shell, so a stale value would make the leg stop after a step-0 save. Submit with the variable cleared (`env -u TK_JOB_START sbatch ...`), let your wrapper set it at the job's own start before the restore, and print it in the steps log; check the first log lines for it.
The launch go follows your RESULTs `quota_workaround` (the kit accepts its home and persistent root through the links on the project space; the second tar verified) and `staging_verified` (every input present with its sha; the exact submit line; a fresh start estimate; free space on the project filesystem). Post them as soon as each is true.
EOF
sed -n 1,60p leg_s1_tree/out/NO_FLAG_MIX.md | cut -c1-260