<!-- recovered by seal_plan: transcript=71f94277 line=27865 utc=2026-11-14T02:47:03.790Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/orchard_cp2/inbox/${N}_ORCH_ORDER_submit_the_fixture_now.md <<'EOF'
# ORCH order: submit the checker's fixture rehearsal now

Your QoS line settles it: the `general` cap is one running GPU and one node per user, not a count of submitted jobs, and pending jobs gain age. So the condition "after job 169367 has ended" in my 0213Z order is lifted: submit the one fixture rehearsal now (bundle aee5221e, binding 7b152ff2), once, with every other condition of 0213Z and the marker-read permission of 0225Z unchanged. Tell evalx's inbox the job id when you submit and when it ends.

If Slurm starts it at once (it needs no GPU) it holds our one node for about 13 minutes; that is accepted. If it is still pending when evalx's job 169367 starts, leave both alone.
EOF
cat > $C/evalx/inbox/${N}_ORCH_WORD_submit_IF_P0_P0_when_the_packet_arrives.md <<'EOF'
# ORCH word: submit the IF-P0 baseline arm (P0) as soon as its packet hand-off is in your inbox

The operator's held QoS line shows the `general` cap is one running GPU and one node per user, not a count of submitted jobs, so jobs may wait in the queue behind your 169367 and gain age.

Lane if_p0 is building the P0 packet now and will put a hand-off note in your inbox (name containing `IF_P0_P0_PACKET_READY`: token, path, size and sha256 of `BATCH.sh`, the two exact `sbatch` argument lists, the result path). When it arrives:
1. Verify `BATCH.sh` against the stated sha256.
2. Check the queue and main's notices as you do before every submission. Main has priority on Orchard: if main has anything queued or running on `general`, do not submit and tell me.
3. Send the identical `BATCH.sh` bytes to `sbatch` standard input twice, as the hand-off says: first with `--test-only`, then the real submission, once. No retry.
4. Post one RESULT with the job id and Slurm's forecast in UTC. After that, treat it like your own jobs: one observation when it starts (staging phases, the preflight and the namespace smoke test), one when it ends, and fetch the bounded result archive from `/home/jjyeung/okit/ifp0_results/<token>/` into `/scratch/jjyeung/orch_cd/if_p0/inbox_results/<token>/` (hash it against `EXIT.json`), then tell me and lane if_p0's inbox.

This word covers arm P0 of seal 8d5bdd730bebb9b317f7d4aa715cfe06981f698eceed13af81f3232d07cd3a90 only. Your own job 169367 keeps its place; do not cancel or reorder anything.
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: orchard_cp2 RESULT 0244Z: both overlap refusals pass on bundle aee5221e; held QoS line general_qos = per-user cap of one running GPU and one node (not a submitted-job count); monitor reloaded to post space events only on floor crossings; removal list updated (cheap-copy objects removable by the user). ORDERS ($N): orchard_cp2 submits the checker fixture now; evalx submits IF-P0 arm P0 (seal 8d5bdd73) as soon as if_p0's packet hand-off arrives, after its queue and main-notice check, test-only first, one real submission. Re-armed evwait (bemzensbz)." >> $C/ORCH_HANDOFF.md; echo $N