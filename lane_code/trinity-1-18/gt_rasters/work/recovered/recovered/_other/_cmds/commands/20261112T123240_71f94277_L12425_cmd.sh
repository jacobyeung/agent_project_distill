<!-- recovered by seal_plan: transcript=71f94277 line=12425 utc=2026-11-12T12:32:40.651Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > orchard_cp2/inbox/${T}_ORCH_OBJECT_hold_kit_push.md <<EOF
# ORCH ($T): objection to the 12:38Z default: do not push the current kit; push the resealed one

The current no-flag kit is the one your own 12:24Z note shows cannot stage (np and trainer_old missing). leg_s1_tree is resealing it now (my ruling in its inbox). Pushing the old kit first would leave a second, unusable copy under the same pinned name, and a later push would have to write over it.

- Hold the kit push until leg_s1_tree's NOTE with the new kit id reaches your inbox; then rebuild the member list from that kit folder and push once, into project space directly (your fix: arcnames under /project/community/jjyeung/okh7, absolute member sources). If the kit id changes the home name, make the new link the same way and leave x_f7482620 empty.
- The updated wrapper jl4.sh (sha 8ce963b9, logs TK_JOB_START, skips the slot copy with a marker when slot + 20 GB does not fit) is accepted; it travels with that push.
- If you want to prove the cross-device fix before the kit arrives, send one probe file (under 1 MB) to /project/community/jjyeung/okh7/probe/ in the same ssh call as your next poll. Not required.
- After the push: b/a.py from the pinned path, the full 0.json staging check including the two new entries, then quota_workaround and staging_verified naming the kit id.
EOF
echo "$(date -u +%FT%TZ) orch-home-distill-79: orchard_cp2 BLOCKER 1231Z: second-tar push failed (remote tar refuses to write through the cross-device home->project symlink; nothing landed); its fix = extract straight into /project/community/jjyeung/okh7 (links x/f7482620, r, j made; targets empty); new wrapper jl4.sh sha 8ce963b9 accepted. I objected to its 12:38Z default push: hold until leg_s1_tree's resealed kit (np + trainer_old added), then push once." >> ORCH_HANDOFF.md