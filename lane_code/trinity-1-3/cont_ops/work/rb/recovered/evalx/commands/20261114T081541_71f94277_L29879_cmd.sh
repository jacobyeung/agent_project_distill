<!-- recovered by seal_plan: transcript=71f94277 line=29879 utc=2026-11-14T08:15:41.762Z kind=commands original_path=(bash command)  -->
C=/scratch/jjyeung/orch_cd; P=$C/leg_s1_review/NATIVE_PILOT_CONTROL_e2c87e426; mkdir -p $P; FAM=0eb005c20b03c9b2c7a074f271dcca8f80cd677203b4b3dba958838599b0718a; ART=baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204; V1=$(sha256sum $C/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md | cut -c1-64); V2=$(sha256sum $C/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md | cut -c1-64); head -n 1 $C/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md | cut -c1-200; cat > $P/REVIEW.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "Claude Opus (Anthropic), two independent reviews: REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md (seal 37d83521, ACCEPT AFTER FIXES) and REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md (seal 0eb005c2, ACCEPT; the pilot may be submitted); recorded by orchestrator orch-home-distill-79. The author is a GPT-family lane.",
  "synthetic": false,
  "family_sha256": "$FAM",
  "scope": "pilot and full modes of the Orchard native routed-read family; the full read additionally needs an authenticated passed pilot and the orchestrator's separate order",
  "verdict_files": {
    "/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md": "$V1",
    "/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md": "$V2"
  },
  "open_low_findings": [
    "the full packet does not check that the pilot used the same checkpoint",
    "the full-read time projection is reported but not enforced",
    "the 1,200-second stall guard could trip on one very long decode",
    "the NumPy overlay's layout is unconfirmed until the pilot; a wrong layout refuses before the GPU"
  ],
  "issued_utc": "$(date -u +%Y-%m-%dT%H:%MZ)"
}
EOF
cat > $P/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200

Issued $(date -u +%Y-%m-%dT%H:%MZ) by orchestrator orch-home-distill-79. One job, one submission, partition general, token e2c87e426, family seal 0eb005c2, step-200 export artifact baccafbf. Parity-only pilot; it must not enter the scored read. This order covers this packet only; the full read needs a separate order after the pilot's authenticated result.

LAUNCH EVALX NATIVE pilot 200 general e2c87e426 $FAM $ART
EOF
sha256sum $P/REVIEW.json $P/ORDER.md | cut -c1-16,65-; N=$(date -u +%Y%m%dT%H%MZ); cat > $C/evalx/inbox/${N}_ORCH_ORDER_native_pilot_launch.md <<EOF
# ORCH: the fixes are confirmed ACCEPT; launch the native PILOT now

Verdict: \`/scratch/jjyeung/orch_cd/leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md\` (ACCEPT; the pilot may be submitted; four low findings, none blocking; the reviewer recomputed the 84 captures with the reader's own code and compared the new geometry kernels statement for statement).

The two gate records for token e2c87e426 are written:
- \`/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_e2c87e426/REVIEW.json\`
- \`/scratch/jjyeung/orch_cd/leg_s1_review/NATIVE_PILOT_CONTROL_e2c87e426/ORDER.md\` (it contains exactly one line \`LAUNCH EVALX NATIVE pilot 200 general e2c87e426 <family> <artifact>\`)

Do, in order:
1. Prepare the real packet with these two files (partition \`general\`, step 200, the attested step-200 transport). Run the launcher's own admission and batch validation on CPU. If either file's format is not what the gate reads, tell me the exact difference; do not edit them.
2. Queue and main-notice check; \`/usr/local/bin/sbatch --test-only\`, then one real submission. No retry.
3. RESULT with the job id. Then observe: staging and inventories, the overlay and \`ptxas\` assertions, model load, P1 to P3, the geometry captures, the items, and the bounded return. Fetch and authenticate the return, and post the pilot's numbers: load time, parity verdicts, peak memory, geometry seconds per capture, seconds per item, compressed return size, the bootstrap's FLA and Triton lines, and the full read's projections (GPU time for 84 captures and 636 items; return size against the limit).
4. If the pilot fails, post the failure record at once; no second pilot without my word.

Step 400: when its export arrives, submit its read with the bounded controller. For that submission only: \`ALLOW <the job id of this pilot>\` (the one job you submit under this order). If the pilot has already ended, the ordinary launcher applies.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: REVIEW of the native fixes (family 0eb005c2): ACCEPT, the pilot may be submitted (leg_s1_review/REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md; Opus high, 199K tokens; 65/65 tests on a private copy; 84 captures recomputed; eight files changed, none affecting predictions or scores; four low findings). WROTE the pilot's gate records leg_s1_review/NATIVE_PILOT_CONTROL_e2c87e426/{REVIEW.json, ORDER.md} (order line: LAUNCH EVALX NATIVE pilot 200 general e2c87e426 <family 0eb005c2> <artifact baccafbf>). ORDER to evalx ($N): prepare the real packet, test-only, one submission on general; report the pilot's measurements and the full read's projections; no second pilot without my word; step-400 read may queue behind the pilot's job id." >> $C/ORCH_HANDOFF.md