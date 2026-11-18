<!-- recovered by seal_plan: transcript=71f94277 line=33633 utc=2026-11-14T21:11:20.015Z kind=commands original_path=(bash command)  -->
O=/scratch/jjyeung/orch_cd/if_p0/out; C=$O/IF8_CONTROL_eef3ba96; SEAL=eef3ba96a639d634be9ec9e976ce16aadec648f4eeb07e2bc6fee196d94516bb; test -e $C && { echo "exists"; exit 1; }; mkdir $C; R=/scratch/jjyeung/orch_cd/leg_s1_review; H1=$(sha256sum $R/REVIEW_VERDICT_IF_P0_KIT.md | cut -c1-64); H2=$(sha256sum $R/REVIEW_VERDICT_IF_P0_JOB_KIT.md | cut -c1-64); H3=$(sha256sum $R/REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md | cut -c1-64); H4=$(sha256sum $R/REVIEW_VERDICT_IF_P0_SEAL_799a21dd.md | cut -c1-64); H5=$(sha256sum $O/P0_CONTROL_eef3ba96/review.md | cut -c1-64); cat > $C/review.md <<EOF
# Cross-family review of the IF-P0 job kit for arm IF8, seal $SEAL

Kit: \`$SEAL\`. Arm: IF8. Permitted partitions: general and advanced. The author is a GPT-family lane; the reviewers are Claude models (Anthropic): Claude Opus for the independent reviews named in part A, and orchestrator orch-home-distill-79 for parts B and C.

## A. Independent reviews that cover IF8's science and job path

- \`/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_IF_P0_KIT.md\` (sha256 $H1): the kit's model, branches, mask, trainable list, sampler, loss and read for all arms; one blocker (head and branches clipped together), fixed.
- \`/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_IF_P0_JOB_KIT.md\` (sha256 $H2), READY: head and branches are clipped separately; P0's branches are built with IF8's seed and frozen, so the two arms differ only in training the branches; the read covers all 52 held-out clips at step 300; the stop rule and the five-degree comparison are as registered. Its minor finding m1 applies to IF8: the admission's compute ratio is not an upper bound (IF8 adds a forward with gradients, a checkpoint recompute and a backward, about four times P0's compute), and the in-job step-8 guard catches an overrun.
- \`REVIEW_VERDICT_IF_P0_SEAL_0fa68201.md\` (sha256 $H3) and \`REVIEW_VERDICT_IF_P0_SEAL_799a21dd.md\` (sha256 $H4), both READY: the later-arm admission of a prior result, partitions and time limits, archive inventories, file modes and the runtime check. All 207 science files stayed byte-identical through these seals.
- The change to the present seal (the CPU load guard off inside a Slurm allocation; step timing through the GPU synchronization) is in \`/scratch/jjyeung/orch_cd/if_p0/out/P0_CONTROL_eef3ba96/review.md\` (sha256 $H5); I hashed both kits and only \`orchard_driver.py\` and \`orchard_compat.py\` changed among the code.

## B. What P0's run at this seal established (Orchard job 169530, return archive sha256 a4877d7c594c484838978ea470717d8f5a6040c87c2becd50d6583122edb126a)

All 300 optimizer updates over 9,600 rows and the read over 52 held-out clips completed in 3 h 08 min; selection sha 4d53d9b8 with the expected skip counts; 86,396 training and 1,664 held-out frames; hidden states and logits bitwise equal at step 0; peak 24.7 GiB allocated. P0's primary direction error is 18.106867996052245 degrees (90% clip-bootstrap interval 16.77 to 19.62), above the registered 12-degree stop threshold. This return is the source for the registered comparison: IF8 passes if it reaches 13.106867996052245 degrees or lower on the same read. IF8 runs at the same seal as P0, so no predecessor-seal exception is used.

## C. What IF8 is the first to execute, and what would show a fault

1. The exact prior-result validator runs inside the IF8 job before large inputs are staged and again before the model loads. A local replay on a different host and Torch build differs from the run in three secondary float fields by at most 1.8e-14; the primary statistic is equal. No tolerance is added to any science file. If the in-job check finds a mismatch on its host, the job refuses in its first minutes; that is a refusal to investigate, not a result.
2. Training the branches: gradients flow through language-model layers 1 to 8. Memory and step time are unmeasured (P0 trained the head only); the sealed budget projects 5.07 to 6.12 hours and the step-8 guard stops an overrun.
3. The decision record compares IF8's read with P0's bound return.

Not checked by me: the 133 CPU tests and the two IF8 drafts' embedded-file verification (author's records).

Verdict: PASS for arm IF8 on general or advanced.
EOF
REP=$(sha256sum $C/review.md | cut -c1-64); cat > $C/confirmation.json <<EOF
{
  "kit_sha256": "$SEAL",
  "report_sha256": "$REP",
  "reviewer": "Claude Opus (independent reviews of the kit and of seals 8df5fb58, 0fa68201 and 799a21dd) and orchestrator orch-home-distill-79 (reading of the change to eef3ba96 and of P0's return for arm IF8)",
  "reviewer_family": "anthropic",
  "schema": "ifp0-cross-family-review-v1",
  "source_identity": {
    "kind": "sealed_tree",
    "kit_sha256": "$SEAL"
  },
  "synthetic": false,
  "verdict": "PASS"
}
EOF
printf 'LAUNCH IF-P0 IF8 %s\n\nPermitted partitions: general and advanced. Packet preparation does not authorize submission; evalx waits for my separate written order.\n' "$SEAL" > $C/launch_note.md
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json;json.load(open('$C/confirmation.json'));print('json ok')"
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/if_p0/inbox/${N}_ORCH_IF8_controls_build_runnable_packets.md <<EOF
# ORCH: IF8 control files supplied; build the runnable packets

Your answers settle the validator question: IF8 checks P0's result exactly inside the job, in the production runtime, and nothing local is blocked; the runtime diff is empty and the seal stays eef3ba96. Good.

Control files: \`$C/\` (review.md, confirmation.json, launch_note.md), in your form. If your admission wants the launch note to hold the one LAUNCH line only, tell me and I rewrite it; do not edit my files.

1. Build the runnable IF8 packets for \`general\` and \`advanced\` with fresh tokens, run the kit's own admission on each with these controls, and hand the \`general\` packet to evalx with a one-line inbox note saying submission waits for my order. One RESULT with tokens and hashes.
2. One risk to state in that RESULT in a single line each: what the in-job prior check does if its recomputed secondary floats differ on the job's host (refuse before staging, with which message), and which measured guard stops IF8 if its step time or memory exceeds the budget.
3. After that, wait for the job's first evidence from evalx as you did for P0.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) if_p0(3) RESULT 2109Z: P0 clears the headroom gate (18.107 deg; 300 steps 35.58 s avg; 3 h 08 min; peak 24.7 GiB). Validator: P0 does not self-validate; IF8 runs the exact validator in-job before staging and before model load (CPU NumPy, production overlay); local builder runs none -> empty runtime diff, seal stays eef3ba96, science table identical. IF8 drafts: general a52c9cd5a1ee16305, advanced ae8ba7e8234793dca; projection 5.07-6.12 h. I wrote IF8 control files if_p0/out/IF8_CONTROL_eef3ba96/ (review citing the four independent reviews + P0 return; confirmation PASS; launch note) and ordered the runnable packets; submission on my order through evalx." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; echo $REP | cut -c1-16