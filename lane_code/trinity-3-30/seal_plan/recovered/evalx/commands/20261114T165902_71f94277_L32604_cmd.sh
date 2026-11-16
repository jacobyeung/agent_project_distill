<!-- recovered by seal_plan: transcript=71f94277 line=32604 utc=2026-11-14T16:59:02.620Z kind=commands original_path=(bash command)  -->
R=/scratch/jjyeung/orch_cd/leg_s1_review; C=$R/NATIVE_PILOT_CONTROL_e54df2d6a; FAM=62a94599cc05478e56986c39edea4c8f82139392a1966d5145b175f09be05bfe; T=$(date -u +%Y-%m-%dT%H:%MZ); cat > $C/ORDER.md <<EOF
# ORCH launch order: Orchard native routed-read PILOT, step 200 (fifth attempt)

Issued $T by orchestrator orch-home-distill-79; it replaces the order of 16:5xZ in this file, whose allowance was incomplete. One job, one submission, partition advanced, token e54df2d6a, family seal 62a94599, step-200 export artifact baccafbf. Standard pilot mode (P1 to P3, five geometry captures, ten item pairs); it must not enter the scored read. Queue allowance for this submission: ALLOW 169530 167739 167857 167858 167859 167860 167861 167894 168278, where every job other than 169530 is one of main's protected jobs and is allowed only while PENDING with reason Dependency or JobHeldUser. Jobs of other users are not this account's concern. This order covers this packet only.

LAUNCH EVALX NATIVE pilot 200 advanced e54df2d6a $FAM baccafbf216a7d708cfaf67f6ec6ef4e20692fa45b88c52809580f986c3d1204
EOF
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/evalx/inbox/${N}_ORCH_RULING_pilot5_allowance_full_protected_set.md <<EOF
# ORCH ruling: the allowance is main's full protected set; submit pilot 5

My allowance named only three of main's jobs. The listing shows the whole protected set, which I knew and should have written: 167739, 167857, 167858, 167859, 167860, 167861, 167894 and 168278, all of user jjyeung, all PENDING with reason Dependency or JobHeldUser. None can start during a ten-minute pilot unless main releases it, and then it waits at most those minutes. The jobs of user aanis belong to another user of the account and are outside the guard's concern: the guard looks at user jjyeung only.

I rewrote \`$C/ORDER.md\` with this allowance (rebind it; REVIEW.json is unchanged). Rule for the submit guard: on \`advanced\`, user jjyeung may have exactly jobs from that set, each PENDING with reason Dependency or JobHeldUser; 169530 on \`general\`. If one of them is RUNNING, or pending for any other reason, or an unknown jjyeung job is there: no submission, one line to me. Otherwise submit now as ordered. If the guard's code needs a change to express this, make it, run its tests, and say so in the event; it can only refuse.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) evalx BLOCKER 1658Z: pilot 5 not submitted: advanced listing shows main's full protected set pending (167739, 167857-167861, 167894, 168278: Dependency or JobHeldUser) plus another user's jobs; my allowance named only three. Rewrote NATIVE_PILOT_CONTROL_e54df2d6a/ORDER.md with the full set (allowed only while PENDING Dependency/JobHeldUser) and told evalx to submit." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md