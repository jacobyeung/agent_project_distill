<!-- recovered by seal_plan: transcript=71f94277 line=32928 utc=2026-11-14T18:39:18.871Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_e702b65e2; FAM=2b9d7815e87d0763eded82e3d47e108d731a43a1367c6230ac4dfaf07e358d1e; test -e $C && { echo exists; exit 1; }; mkdir $C; T=$(date -u +%Y-%m-%dT%H:%MZ); cat > $C/REVIEW.json <<EOF
{
  "verdict": "ACCEPT",
  "reviewer": "Claude Opus (Anthropic), independent reviews REVIEW_VERDICT_ORCHARD_NATIVE_FAMILY.md, REVIEW_VERDICT_ORCHARD_NATIVE_FIXES.md, REVIEW_VERDICT_NATIVE_PROBE_FIX.md, REVIEW_VERDICT_NATIVE_P1_GATE.md and the independent audit NATIVE_PIN_GRAPH_AUDIT.md (46 checks; findings #35 and #42); orchestrator orch-home-distill-79 (Claude) verified this reseal. The author is a GPT-family lane.",
  "synthetic": false,
  "family_sha256": "$FAM",
  "scope": "pilot and full modes; the full read additionally needs an authenticated passed pilot of this exact family and the orchestrator's separate order",
  "reseal_check": {
    "previous_family_sha256": "62a94599cc05478e56986c39edea4c8f82139392a1966d5145b175f09be05bfe",
    "why": "pilot job 169589 was refused by the bootstrap: the runtime spec pinned the old worker hash; the audit also found the mask cache bound to a reader hash that matches no sealed reader",
    "what_i_checked": [
      "against the previous family 28 pinned values differ: assets.worker_entrypoint is now 8611b515 and equals the code pin of native_worker.py; worker_contract.mask_cache names the new receipt 709990e5; the code object (code_fd3b8cc4a94e446d.tar, generation 1794680410160761) adds that receipt, native_cpu_replica.py and native_pin_graph.py and carries the changed native_launcher.py and native_local_check.py; the reader, worker, job and metrics pins are unchanged",
      "the old and new mask receipts (1,248 values each) differ in exactly one value, producer_sha256, and the new value equals the sealed reader pin 6b61d819; the kernel source pin equals the code pin",
      "the 46-row record REUSE_COMPARISONS.json (sha f92a1b20): 14 executed locally, 9 statically proved, 13 covered by a named earlier pilot, 6 live only, all passed; rows 7, 8, 28 and 36 wait only for these control files"
    ],
    "not_checked": "the 111 family tests and 9 reuse-gate tests, the reuse receipt's hash walk and the upload receipts (author's records); the new submission-side helpers were not independently reviewed (they can only refuse); pilot 6 is the first job to run the bootstrap entrypoint check with these pins, the P1 gate on a GPU, the mask check, the five captures and ten item pairs, and to publish the report"
  },
  "issued_utc": "$T"
}
EOF
cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200 (sixth attempt)

Issued $T by orchestrator orch-home-distill-79. One job, one submission, partition advanced, token e702b65e2, family seal 2b9d7815, step-200 export artifact baccafbf. Standard pilot mode (P1 to P3, five geometry captures, ten item pairs); it must not enter the scored read. Queue allowance for this submission: ALLOW 169530 167739 167857 167858 167859 167860 167861 167894 168278, where every job other than 169530 is one of main's protected jobs and is allowed only while PENDING with reason Dependency or JobHeldUser. Jobs of other users are not this account's concern. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 200 advanced e702b65e2 $FAM baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json;json.load(open('$C/REVIEW.json'));print('json ok')"
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_native_pilot_6_launch_advanced.md <<EOF
# ORCH order: launch native pilot 6 on \`advanced\` (token e702b65e2, family 2b9d7815)

Verified by me: the two mask receipts differ only in producer_sha256, now the sealed reader pin; the worker entrypoint equals the code pin; against family 62a94599 only the expected 28 values changed; your 46-row record has every row passed except the four that wait for these controls. Control files: \`$C/REVIEW.json\` and \`$C/ORDER.md\`.

1. Run the reuse gate and the unchanged sealed admission with these controls, then one test-only call and one real submission on \`advanced\`, with the same account rule as pilot 5 (main's eight protected jobs only while PENDING for Dependency or JobHeldUser; 169530 on \`general\`). Anything else: no submission, one line to me. No retry.
2. Not running within 20 minutes: one line with the pending reason.
3. RESULT when it returns, gate outcome first (sealed P1, p1_gate and its ties, P2 with its independent call count, P3, the probe's calls), then load time, peak memory, the mask check, geometry seconds per capture, seconds per item pair, return size, the first camera, distance and room item traces with answers against labels and the call and version error counts, and the full-read projection for 636 items over 84 captures on both partitions against time, return size and the pool's remaining 874 MB.
4. On a pass: build the full-read packets for both partitions from this exact family and report their tokens. I order the full read separately.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx RESULT 1837Z: pilot-6 candidate checked through the reuse path: family 2b9d7815, advanced token e702b65e2, code object code_fd3b8cc4a94e446d.tar gen 1794680410160761; 46 rows (14 local, 9 static, 13 earlier-pilot, 6 live-only passed; 4 wait for controls); Orchard return pool 200 MB used, 874 MB free. I verified: mask receipts differ only in producer_sha256 (-> 6b61d819 = reader pin); worker_entrypoint == code pin; 28 expected changed values vs 62a94599. Control files leg_s1_review/NATIVE_PILOT_CONTROL_e702b65e2/. ORDERED pilot 6 on advanced." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md