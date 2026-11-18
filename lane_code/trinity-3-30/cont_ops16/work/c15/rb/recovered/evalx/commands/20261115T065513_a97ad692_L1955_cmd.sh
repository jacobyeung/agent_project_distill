<!-- recovered by seal_plan: transcript=a97ad692 line=1955 utc=2026-11-15T06:55:13.419Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd; C=$R/leg_s1_review/NATIVE_PILOT_CONTROL_ebe307cf4; mkdir -p $C; T=$(date -u +%Y-%m-%dT%H:%MZ); PK=$R/evalx/work/milestone/native_package_s24_05/pilot_candidate_advanced/PACKET.json; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "
import json
d=json.load(open('$PK'))
for k in ('mode','partition','step','token','artifact','artifact_sha256','family','family_sha256','gpus'):
    if k in d: print(k, str(d[k])[:120])
print(list(d.keys())[:25])
"; cat > $C/REVIEW.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "Claude Opus (Anthropic), independent read-only review REVIEW_VERDICT_PILOT9_COVERAGE.md (SUBMIT WITH NOTED RISKS; sha256 3e8fbe85b8d46a83c2f22a1235c4ef2ed06a6dec6588b0391a8d4ea4ca305cdb), with the earlier reviews of this reader; orchestrator orch-home-distill-49 (Claude) read the runtime diff. The author is a GPT-family lane.",
  "synthetic": false,
  "family_sha256": "3688e98758d834254fa3066f76687321ee42e91f7f8535b4460004746c8d70af",
  "scope": "pilot mode only, for the step-544 stop export (artifact 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef), partition advanced, token ebe307cf4; this family does not fly a full read: the full reads run on a later family after its own pilot",
  "followup_diff_read": {
    "diff": "/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/RUNTIME_DIFF_97f1297b_02.patch (sha256 6e01c6e9a9ea13b203bf96291eebe0cfb3bac655d54f8c4ac0294da39fe24f21; one changed line against family 97f1297b)",
    "what_i_checked": [
      "the one changed line: native_worker.py:155 calls geometry_cohort(G, worker[\"geometry_captures\"]) instead of geometry_cohort(G, worker), the wrong argument on which job 169687 died after passing every gate",
      "the independent review confirmed that all 44 code.tar members equal sources/ byte for byte, that every copy of the worker (079f876a) and of the code object (4d05c37b294797877128c13c32e64ca6a19ac9b148a444f6936c432a069ccef8, 3,584,000 bytes) carries the new value, that the seven CPU stand-ins agree with the real call sites, and that the real Masks constructor accepts the production mask receipt",
      "PILOT9_REVIEW_READY.json binds this family, token ebe307cf4, the code object 4d05c37b and worker 079f876a; the upload is confirmed at generation 1794724906618876 and was never restarted",
      "the review classified all 692 unexecuted lines: 445 cannot run in pilot mode, 119 run only on a fault, 128 may run, of which 79 already ran on a GPU in job 169687 with unchanged bytes"
    ],
    "not_checked": "the family seal was computed after the independent review, from the sources it read; the author's sealed-family four-return tests and the 1,170-member reuse proof were not rerun by me. Stated risks that only the GPU tests: R2 real-head geometry on the 79 captures never run on a GPU and any geometry error other than reference_camera_up_opposes_gravity; R4 the budget cap firing through the worker; R5 forced closing with the real tokenizer. Stated pilot-only risks: R1 a program_refusal row raises in the pilot projection; R3 the 2,400 s limit is exceeded if most of the twenty decodes run to the cap."
  },
  "issued_utc": "$T"
}
EOF
cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 544 (ninth pilot; plumbing check of the corrected worker)

Issued $T by orchestrator orch-home-distill-49. One job, one submission, partition advanced, token ebe307cf4, family seal 3688e987, step-544 stop export artifact 1d6eeb28. Pilot mode: P1 to P3, geometry for all 84 captures, ten item pairs; it must not enter the scored read, and this family flies no full read. Queue allowance for this submission: ALLOW 167739 167857 167858 167859 167860 167861 167894 168278, each one of the other project's protected jobs, allowed only while PENDING with reason Dependency or JobHeldUser; on general no job of ours. Jobs of other users are not this account's concern. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 544 advanced ebe307cf4 3688e98758d834254fa3066f76687321ee42e91f7f8535b4460004746c8d70af 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json; json.load(open('$C/REVIEW.json')); print('REVIEW.json parses')"
I=$R/evalx/inbox/$(date -u +%Y%m%dT%H%MZ)_ORCH_ORDER_native_pilot_9_launch_advanced_ebe307cf4.md; cat > $I <<EOF
# ORCH order: launch native pilot 9 on \`advanced\` (token ebe307cf4, family 3688e987)

I read your 0652Z RESULT and the one-line runtime diff; the independent coverage review stands (SUBMIT WITH NOTED RISKS). Control files: \`$C/REVIEW.json\` and \`$C/ORDER.md\`. The shared Orchard master is restored (06:55Z).

1. The reuse gate and the unchanged sealed admission with these controls, then the accepted launch transaction on \`advanced\`. Account rule as in ORDER.md. Anything else: no submission, one line to me. No retry.
2. Launch cadence: check process and job state once a minute after submission; not running within 20 minutes: one line with the pending reason. Once it runs, routine observations ten minutes apart as your status says.
3. RESULT when it ends: the gate; the 84-capture table with counts by dataset and the geometry refusals by code; the ten pairs for both arms with the refused pair's records; whether the budget cap fired on any decode and how the forced close behaved (R4, R5); any program_refusal (R1); wall time against the 2,400 s limit (R3); return size; or, on failure, the failing line and what was published.
4. This family flies no full read. The separate candidate (guard as a post-authentication reader override, R1, 6,000 s limit, selector) continues; its uploads and seal still need my order.
5. Rotation is unchanged: draft and ROTATION_READY by 07:15Z. If the pilot is still running at rotation, the draft tells the successor exactly how to observe, fetch and report it, and what never to resubmit.
EOF
echo "- $T PILOT 9 SEALED (evalx RESULT 0652Z): the code upload was admitted and confirmed (generation 1794724906618876); family 3688e98758d834254fa3066f76687321ee42e91f7f8535b4460004746c8d70af, advanced token ebe307cf4. Orchard master restored 06:55Z. Wrote leg_s1_review/NATIVE_PILOT_CONTROL_ebe307cf4/{REVIEW.json, ORDER.md} (scope: pilot only) and ordered the launch ($(basename $I))." >> $R/ORCH_HANDOFF.md; ls $C