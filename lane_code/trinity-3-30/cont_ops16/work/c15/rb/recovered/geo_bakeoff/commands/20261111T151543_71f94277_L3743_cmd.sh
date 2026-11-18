<!-- recovered by seal_plan: transcript=71f94277 line=3743 utc=2026-11-11T15:15:43.928Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); cat > geo_bakeoff/inbox/${T}_ORCH_ANSWER_weight_io.md <<'EOF'
# ORCH ANSWER: yes, download the five checkpoints (19.9 GB), with one change
- Use `curl -L --limit-rate 5M` (not 8M): another lane reads 4.6 GB from /data* this hour and the data mover's copies share the account's 20 MB/s; one file at a time, the free-space gate before each, sha256 or size check after each against the API's numbers.
- If a curl is killed or a connection drops, do not retry in a loop: post a BLOCKER with what happened and carry on with CPU work on what has arrived.
- Order: the smallest first (MoGe-2, MoGe-3), so exporters can be smoke-tested while the large ones arrive.
EOF
echo "$(date -u +%Y-%m-%dT%H:%MZ) geo_bakeoff QUESTION weight_io: approved 19.9 GB of weights (MapAnything 4.9, DA3 nested giant 6.8, Pi3X 5.4, MoGe-2 1.3, MoGe-3 1.5 GB) at 5 MB/s, one curl at a time, smallest first (within the brief's 40 GB cap and the standing no-ask rule for downloads under 100 GB)." >> ORCH_HANDOFF.md