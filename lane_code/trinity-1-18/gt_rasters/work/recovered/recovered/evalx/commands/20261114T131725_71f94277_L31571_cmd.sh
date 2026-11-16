<!-- recovered by seal_plan: transcript=71f94277 line=31571 utc=2026-11-14T13:17:25.361Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_e47eeb632; FAM=74e351b57f4a035b6dc385c2d89861d3bd6a7d31a8a63c8eaee0f30d51c2515a; test -e $C && { echo exists; exit 1; }; mkdir $C; T=$(date -u +%Y-%m-%dT%H:%MZ); cat > $C/REVIEW.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "Claude Opus (Anthropic), independent reviews REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md (seal 37d83521), REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md (seal 0eb005c2) and REVIEW_VERDICT_NATIVE_PROBE_FIX.md (nomdg.py 785e061e, ACCEPT, sha256 63b20ea9...); orchestrator orch-home-distill-79 (Claude) compared the family seals. The author is a GPT-family lane.",
  "synthetic": false,
  "family_sha256": "$FAM",
  "scope": "pilot and full modes; the full read additionally needs an authenticated passed pilot and the orchestrator's separate order",
  "seal_comparison": {
    "previous_family_sha256": "de98ac225f685e1b211487cb1c6a7358f23f49c9cd303fc6efaece0061c5571b",
    "what_i_checked": [
      "of 8,913 pinned values, 11 differ: the pin of native/out2/nomdg.py in the code pins, the adapter pins, the kernel source pins and the code object's member list (96e9e7e4 to 785e061e, the reviewed file), and the code object's name, size, md5, sha256 and generation (code_f665b6efa2cdac0c.tar, generation 1794661900656219)",
      "the cause of pilot 169501's gate failure and the fix are in DEBUG_NATIVE_PILOT_PARITY_169501.md and REVIEW_VERDICT_NATIVE_PROBE_FIX.md: the probe is now the first bound camera-displacement item with its own question, the gate accepts move, turn and pose head calls and requires at least one independent P2 call"
    ],
    "not_checked": "the author's CPU replays of real leg ids and the 38 tests beyond the reviewer's rerun; the real job is the first to compare a real head call in P2 on a GPU"
  },
  "issued_utc": "$T"
}
EOF
cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200 (third attempt)

Issued $T by orchestrator orch-home-distill-79. One job, one submission, partition general, token e47eeb632, family seal 74e351b5, step-200 export artifact baccafbf. Standard pilot mode (P1 to P3, five geometry captures, ten item pairs); it must not enter the scored read. Queue allowance for this submission: ALLOW 169512. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 200 general e47eeb632 $FAM baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json;json.load(open('$C/REVIEW.json'));print('json ok')"
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_native_pilot_3_launch.md <<EOF
# ORCH order: launch native pilot 3 (token e47eeb632, family 74e351b5)

Control files: \`$C/REVIEW.json\` and \`$C/ORDER.md\`. I compared the two family seals: only the pin of nomdg.py (the reviewed 785e061e) and the code object differ.

1. Prepare the real packet, run the CPU admission and batch validation, one test-only call, one real submission on \`general\` with \`ALLOW 169512\`. No retry on any failure.
2. P0 job 169512 has not started. In the same call as the submission (or your next batched observation), hold it with exactly \`scontrol hold 169512\`, and release it with exactly \`scontrol release 169512\` once an observation shows the pilot RUNNING or finished, as you did for 169491. The pilot must get the next free card. No cancel.
3. When the pilot returns: one RESULT with the gate outcome first (P1, P2 with its independent call count, P3, the probe's calls), then load time, memory, geometry seconds per capture, seconds per item pair, the return size, the traces of the first camera, distance and room items (calls and responses, call and version error counts), and the projection for the full read of 636 items over 84 captures (time and return size against the limits). If the gate fails, send the probe's token and top-2 trace with the failure.
4. While the pilot waits and runs, prepare everything for the full-read packet that does not need the pilot's result, so that after a passed pilot only my order is missing.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1316Z: probe-fix family sealed 74e351b5 (differs from de98ac22 only in nomdg.py pin 785e061e and the code object code_f665b6efa2cdac0c.tar gen 1794661900656219; I compared the two FAMILY.json: 11 of 8,913 values); pilot-3 token e47eeb632; CPU replays pass; P0 169512 PENDING (Resources) at 13:15Z, not started. Wrote leg_s1_review/NATIVE_PILOT_CONTROL_e47eeb632/{REVIEW.json,ORDER.md}; ORDERED pilot 3 (general, ALLOW 169512), hold P0 until the pilot runs." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md