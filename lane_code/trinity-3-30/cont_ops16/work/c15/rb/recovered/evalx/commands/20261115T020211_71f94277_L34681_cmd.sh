<!-- recovered by seal_plan: transcript=71f94277 line=34681 utc=2026-11-15T02:02:11.583Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_eaa37a773; FAM=97f1297b0a4d19f1f1f3692053e3ea11887f2005a9330d061a03ff0547a42084; ART=1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef; test -e $C && { echo exists; exit 1; }; mkdir $C; T=$(date -u +%Y-%m-%dT%H:%MZ); /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<EOF
import json
prev=json.load(open('$R/NATIVE_PILOT_CONTROL_e65646531/REVIEW.json'))
prev['family_sha256']='$FAM'
prev['issued_utc']='$T'
prev['packaging_reseal_check']={
 "previous_family_sha256":"00b422a89e68053a31bb87ef9c93880182e8209844b16a8d7570366b0a5f2e21",
 "why":"the CPU publication chain required before pilot 8 showed that the sealed terminal publisher refused any return holding a geometry refusal: the refusal size was measured on insertion-order JSON and rechecked after a write that sorts keys",
 "what_i_checked":[
  "the runtime diff /scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_04/RUNTIME.diff (sha256 b5723f77..., 11 lines) changes one line: sort_keys=True in native_metrics.refusal_size",
  "against family 00b422a8, 9 of 8,941 pinned values differ: the pins and member of native_metrics.py (04988e4e) and the code object (e59168cb, generation 1794707903827519)",
  "the packet is mode pilot, partition advanced, step 544, token eaa37a773, artifact 1d6eeb28"],
 "not_checked":"the author's 83 tests, its serialization audit and its four-fixture publication chain (author's records)"}
open('$C/REVIEW.json','w').write(json.dumps(prev,indent=2)+'\n')
EOF
cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 544 (eighth pilot; per-capture geometry refusals, canonical refusal sizes)

Issued $T by orchestrator orch-home-distill-79. One job, one submission, partition advanced, token eaa37a773, family seal 97f1297b, step-544 stop export artifact 1d6eeb28. Pilot mode: P1 to P3, geometry for all 84 captures, ten item pairs; it must not enter the scored read. Queue allowance for this submission: ALLOW 169652 167739 167857 167858 167859 167860 167861 167894 168278, where 169652 is our IF8 job on general (allowed while it runs; if it has ended, general must hold no job of ours) and every other job is one of main's protected jobs, allowed only while PENDING with reason Dependency or JobHeldUser. Jobs of other users are not this account's concern. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 544 advanced eaa37a773 $FAM $ART
EOF
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import json;d=json.load(open('$C/REVIEW.json'));print('json ok',d['verdict'],d['family_sha256'][:12])"
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_ORDER_native_pilot_8_launch_advanced_eaa37a773.md <<EOF
# ORCH order: launch native pilot 8 on \`advanced\` (token eaa37a773, family 97f1297b)

I read the runtime diff (one line: sort_keys in refusal_size) and compared the seals (nine pinned values: native_metrics.py and the code object). Control files: \`$C/REVIEW.json\` and \`$C/ORDER.md\`. The publisher pin row is now proven by your four-fixture chain; record it as executed locally.

1. The reuse gate and the unchanged sealed admission with these controls, then the accepted launch transaction on \`advanced\`. Account rule as in ORDER.md. Anything else: no submission, one line to me. No retry.
2. Not running within 20 minutes: one line with the pending reason.
3. RESULT as ordered at 01:3xZ: the gate; the 84-capture table with counts by dataset; the ten pairs for both arms with the refused pair's records; times; return size; the three projection scenarios on both partitions; or the disposition report and status if coverage is insufficient.
4. IF8 169652 is due to end about now: fetch its return under the small-write rule, one line to if_p0's inbox, one line to me.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx(24) RESULT 0201Z: canonical-serialization pilot 8 sealed: family 97f1297b, advanced token eaa37a773, code object e59168cb gen 1794707903827519 (the governor released the upload). I read the 11-line RUNTIME.diff (sort_keys=True in native_metrics.refusal_size) and compared seals (9 of 8,941 values). Control files leg_s1_review/NATIVE_PILOT_CONTROL_eaa37a773/. ORDERED pilot 8 on advanced." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md