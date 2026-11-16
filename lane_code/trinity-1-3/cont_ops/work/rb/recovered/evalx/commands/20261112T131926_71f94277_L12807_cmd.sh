<!-- recovered by seal_plan: transcript=71f94277 line=12807 utc=2026-11-12T13:19:26.605Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd; T=$(date -u +%Y%m%dT%H%MZ); for l in orchard_port orchard_cp2; do cat > $l/inbox/${T}_ORCH_RELEASE_streams_orchard_writes_still_held.md <<EOF
# ORCH ($T): main released the stream pause; writes to Orchard stay held until it has space

Main wrote at 13:18Z (USER clarification): its download runs under a separate allowance, so our governed streams may run again, each copy at 10 MB/s or less (keep your governed pace). Two holds remain:
1. Orchard /project/community read 0 bytes free at 13:10Z and /home is at quota: push nothing to Orchard until a poll shows at least 150 GB free in the project space (the user has the removal lists). Pulls from Orchard to Trinity and Trinity-local governed copies may run.
2. Submit nothing to the advanced partition until I write a GO (main holds one card until about 14:00Z).
EOF
done
cat > evalx/inbox/${T}_ORCH_RELEASE_streams.md <<EOF
# ORCH ($T): the stream pause is lifted
Main released it at 13:18Z. Governed copies may run again, each at 10 MB/s or less. Nothing goes to Orchard: its project space is full.
EOF
echo 100 > /tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad/notices_seen.txt; echo "$(date -u +%FT%TZ) orch-home-distill-79: main's notice 13:18Z (USER clarification: main's download has its own 20 MB/s allowance; other copies share a 20 MB/s limit, each <= 10 MB/s): stream pause lifted for orchard_port, orchard_cp2, evalx; Orchard writes stay held (project space 0 B free) and advanced submits stay held (main's card until ~14:00Z)." >> ORCH_HANDOFF.md