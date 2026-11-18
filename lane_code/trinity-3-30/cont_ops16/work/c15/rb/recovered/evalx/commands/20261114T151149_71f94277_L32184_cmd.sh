<!-- recovered by seal_plan: transcript=71f94277 line=32184 utc=2026-11-14T15:11:49.700Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_e3e6c6421; FAM=e2374d642151d63d18e88920f9a0aa7ae861b4aefe588bfde27bee29362ab2ec; test -e $C && { echo exists; exit 1; }; mkdir $C; T=$(date -u +%Y-%m-%dT%H:%MZ); cat > $C/REVIEW.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "Claude Opus (Anthropic), independent reviews REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md, REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md, REVIEW_VERDICT_NATIVE_PROBE_FIX.md and REVIEW_VERDICT_NATIVE_P1_GATE.md (ACCEPT AFTER FIXES on family e58e5a1e: findings F1 and F2); orchestrator orch-home-distill-79 (Claude) confirmed the follow-up diff. The author is a GPT-family lane.",
  "synthetic": false,
  "family_sha256": "$FAM",
  "scope": "pilot and full modes; the full read additionally needs an authenticated passed pilot and the orchestrator's separate order",
  "followup_diff_read": {
    "diff": "/scratch/jjyeung/orch_cd/evalx/work/milestone/native_p1_s23_02/RUNTIME.diff (sha256 3b2c1ad39d29af47..., 63 lines)",
    "previous_family_sha256": "e58e5a1e4bf0332a8b0764efed9618c7ecb6beab9c293de1359f0ab9ab30522f",
    "what_i_checked": [
      "F1: native_worker.py no longer builds the report object before the parity kernel; it prints a pilot_loaded line after restoration and builds the report with its loaded checkpoint inside the finally that follows the parity kernel, so the kernel's exclusive mkdir runs first",
      "F2: in nomdg.py's P1 gate a mismatch with a missing cached record, missing fields, non-integer ids or non-finite logits or margins is counted as rejected instead of raising; the tie rule (equal top-2 sets, both margins at most 1.0, cap max(1, checked // 100)) is unchanged",
      "the two family seals differ in 12 of 8,913 pinned values: the pins of nomdg.py (6b61d819) and native_worker.py (8611b515) and the code object (code_0521775d7ee21337.tar, generation 1794668957175340); the on-disk files hash to those pins"
    ],
    "not_checked": "the author's 68 CPU tests, including the new test that runs the real parity kernel through its mkdir; pilot 4 is the first real job to evaluate p1_gate on a GPU and to publish the report"
  },
  "issued_utc": "$T"
}
EOF
cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200 (fourth attempt)

Issued $T by orchestrator orch-home-distill-79. One job, one submission, partition advanced, token e3e6c6421, family seal e2374d64, step-200 export artifact baccafbf. Standard pilot mode (P1 to P3, five geometry captures, ten item pairs); it must not enter the scored read. Queue allowance for this submission: ALLOW 169526 169530. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 200 advanced e3e6c6421 $FAM baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json;json.load(open('$C/REVIEW.json'));print('json ok')"
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_native_pilot_4_launch_advanced.md <<EOF
# ORCH order: launch native pilot 4 on \`advanced\` (token e3e6c6421, family e2374d64)

I read the follow-up diff (F1 in the worker, F2 in the gate) and compared the seals: confirmed. Control files: \`$C/REVIEW.json\` and \`$C/ORDER.md\`.

1. Real packet, CPU admission and batch validation, one test-only call, one real submission on \`advanced\` with \`ALLOW 169526 169530\`. No retry. The general fallback (ee49236ff) stays unsubmitted.
2. If the scheduler does not start it within 20 minutes, tell me in one line with the pending reason; do not move it yourself.
3. RESULT when it returns, gate outcome first (the sealed P1 result, p1_gate with its tie list, P2 with its independent call count, P3, the probe's calls), then load time, peak memory, geometry seconds per capture, seconds per item pair, return size, the traces of the first camera, distance and room items (calls, responses, call and version error counts, the answers against the labels), and the full-read projection for 636 items over 84 captures against the time and return-size limits on \`advanced\` and on \`general\`.
4. If it passes, build the full-read packet for \`advanced\` at once and report its token; I order it separately. Main's orchestrator has been told the allocation is free for it, so a full read there needs my word first.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1509Z: F1/F2 fixed, family e2374d64 (vs e58e5a1e: nomdg.py 6b61d819, native_worker.py 8611b515, code object code_0521775d7ee21337.tar; 12 of 8,913 values; I read RUNTIME.diff 3b2c1ad3 and compared seals: CONFIRMED). Control files leg_s1_review/NATIVE_PILOT_CONTROL_e3e6c6421/. ORDERED pilot 4 on advanced (token e3e6c6421; ALLOW 169526 169530)." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md