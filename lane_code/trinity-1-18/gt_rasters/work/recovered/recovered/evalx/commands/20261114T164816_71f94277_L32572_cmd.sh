<!-- recovered by seal_plan: transcript=71f94277 line=32572 utc=2026-11-14T16:48:16.941Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_e54df2d6a; FAM=62a94599cc05478e56986c39edea4c8f82139392a1966d5145b175f09be05bfe; test -e $C && { echo exists; exit 1; }; mkdir $C; T=$(date -u +%Y-%m-%dT%H:%MZ); cat > $C/REVIEW.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "Claude Opus (Anthropic), independent reviews REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md, REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md, REVIEW_VERDICT_NATIVE_PROBE_FIX.md and REVIEW_VERDICT_NATIVE_P1_GATE.md (findings F1 and F2, fixed in family e2374d64 and confirmed by the orchestrator's diff reading); orchestrator orch-home-distill-79 (Claude) verified this packaging-only reseal. The author is a GPT-family lane.",
  "synthetic": false,
  "family_sha256": "$FAM",
  "scope": "pilot and full modes; the full read additionally needs an authenticated passed pilot and the orchestrator's separate order",
  "packaging_reseal_check": {
    "previous_family_sha256": "e2374d642151d63d18e88920f9a0aa7ae861b4aefe588bfde27bee29362ab2ec",
    "why": "pilot job 169537 failed at input-pin validation: the uploaded code object still held the old bytes of native_job.py, native_metrics.py and native_worker.py",
    "what_i_checked": [
      "every one of the 34 code pins has a member in the new code object (code_698766e61697edf0.tar, generation 1794674563840719) with the same sha256; no pin lacks a member; the five members without a code pin are support files",
      "against the previous family, the reader (nomdg.py 6b61d819), the worker (8611b515), the job (a51754f4) and the metrics module (e797b4b3) keep their reviewed pins; only native_launcher.py (the submit guard) changed and native_local_check.py was added, both submission-side",
      "the author's local check record states that the job's own stager extracted the five exact uploaded objects and its own pin validation passed on them, and that the runtime-import bootstrap files are byte-identical to pilot 169521's"
    ],
    "not_checked": "the 63 CPU tests and the local check's execution (author's records); the submit guard's code was not independently reviewed (it can only refuse a submission)"
  },
  "issued_utc": "$T"
}
EOF
cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200 (fifth attempt)

Issued $T by orchestrator orch-home-distill-79. One job, one submission, partition advanced, token e54df2d6a, family seal 62a94599, step-200 export artifact baccafbf. Standard pilot mode (P1 to P3, five geometry captures, ten item pairs); it must not enter the scored read. Queue allowance for this submission: ALLOW 169530 167859 167860 167861, the last three only while each is PENDING with reason Dependency on advanced. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 200 advanced e54df2d6a $FAM baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json;json.load(open('$C/REVIEW.json'));print('json ok')"
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_native_pilot_5_launch_advanced.md <<EOF
# ORCH order: launch native pilot 5 on \`advanced\` (token e54df2d6a, family 62a94599)

I verified the reseal myself this time: all 34 code pins have a member with the same hash in the new code object, and against the previous family only the launcher guard changed and the local check was added. Control files: \`$C/REVIEW.json\` and \`$C/ORDER.md\`.

1. Run the permanent submit guard (the local proof, the real early admission, the unchanged validate_config with these controls), then one test-only call and one real submission on \`advanced\`. The fresh listing must show for this account on \`advanced\` only 167859, 167860 and 167861, each PENDING with reason Dependency; 169530 is allowed on \`general\`. Anything else: no submission, one line to me. No retry.
2. If it is not running within 20 minutes, one line with the pending reason; do not move it.
3. RESULT when it returns, as ordered for pilot 4: the gate outcome first (sealed P1, p1_gate with its ties, P2 with its independent call count, P3, the probe's calls), load time, peak memory, geometry seconds per capture, seconds per item pair, return size, the first camera, distance and room item traces with their answers against the labels, and the full-read projection for 636 items over 84 captures on both partitions.
4. On a pass, build the full-read packets for both partitions and report their tokens. I order the full read separately.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1647Z: pilot-5 package ready: family 62a94599, code object code_698766e61697edf0.tar gen 1794674563840719, advanced token e54df2d6a (general e5e6cfc9d); local exact-object check PASSES (five objects staged by the job's own stager; pin validation; bootstrap files equal pilot 169521's); 63 CPU tests. I verified: 34/34 code pins have equal members; vs e2374d64 only native_launcher.py changed and native_local_check.py added. Control files leg_s1_review/NATIVE_PILOT_CONTROL_e54df2d6a/. ORDERED pilot 5 on advanced (allow 169530 and main's Dependency-pending 167859-61)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md