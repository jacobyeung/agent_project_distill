<!-- recovered by seal_plan: transcript=71f94277 line=30718 utc=2026-11-14T10:29:53.511Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); cat > /scratch/jjyeung/orch_cd/orchard_cp2/inbox/${N}_ORCH_TASK_prepare_rotation_now.md <<'EOF'
# ORCH task: prepare your rotation now (your session ends by itself at about 13:01Z)

Your process runs under a session limit of 86,000 s and has used about 77,000 s. It would end at about 13:01Z, before the trainer's stop (~14:25Z) and the end runbook. I rotate you now, in the quiet stretch before the next save (~11:58Z).

Do these, in this order, within about ten minutes:
1. Bring `BRIEF_SUCCESSOR13_DRAFT.md` current as the successor's whole operating brief (it will be launched with that file as its brief, unchanged) and bring `STATUS.md` current. Keep both as short as the facts allow; the successor must not need any other file to take over, only to look things up.
2. In the draft, state plainly: the watcher's pid, socket and log; whether the watcher keeps running when your process ends; how the successor verifies it is alive from local files only; and what the successor does if it is not. I authorize the successor one watcher restart through the existing shared ssh master if the watcher is found dead (no new master; on a closed handshake it stops and tells me). The master was recreated at 09:26:03Z and lives about 12 h; only I recreate it.
3. In the draft, list the remaining dated duties with their expected UTC times: saves (next ~11:58Z, ~13:59Z), the trainer's stop and final stop export (~14:25-14:30Z) with its attestation to evalx (`stop_export: true`, the claim read of at most 64 B), the approved read-only end audit step, the end runbook through 15:25Z, and the floor alarms (400, 300, 200, 140 GB, confirmed samples only).
4. Post one event `ROTATION_READY` with the draft's sha256 and the watcher answer from item 2. Then do nothing more: no ssh, no file changes. I end your process and launch the successor right after.

Nothing about job 169097 changes. Send it no signal.
EOF
echo "- $(date -u +%Y-%m-%dT%H:%MZ) Ordered orchard_cp2 s12 to prepare rotation (inbox ${N}_ORCH_TASK_prepare_rotation_now.md): draft 13 current, watcher survival stated, ROTATION_READY event; I then end pid 311906 and launch s13." >> /scratch/jjyeung/orch_cd/ORCH_HANDOFF.md; echo $N