#!/bin/bash
set -u
W=/scratch/jjyeung/orch_n30/seal_plan/work
P=/home/jjyeung/.claude/projects/-scratch-jjyeung-orch-home-distill
R=/data3/jjyeung/orch_n13_20261026/io_governor/REGISTER.md
D=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918
OWNER=seal_plan_transcript_read_1115
NOW=$(date -u +%FT%TZ); ST=$(date -u +%Y%m%dT%H%M%SZ)
echo "- $NOW Distillation lane seal_plan (trinity-3-30): hand stream $OWNER on trinity-3-30, 82,012,539 bytes (two orchestrator transcripts) read from /home at 4 MB/s (pv -q -L 4m) straight into a parser on /scratch, no NFS write; expected end within 1 minute. Start no copy until its STREAM ENDED line appears in REGISTER.md." >> /data3/jjyeung/mover_20261111/DISCUSSION.md
echo "$NOW distillation lane seal_plan, hand stream under OUTAGE_20261115T1000Z.md: $OWNER on trinity-3-30, 82,012,539 bytes read from /home at 4 MB/s (pv -q -L 4m) into a parser, no NFS write; expected end within 1 minute. Start no copy until its STREAM ENDED line appears in REGISTER.md." > $D/INBOX_TO_DISTILL_ORCH_${ST}_seal_plan_hand_copy.md
echo "- $NOW STREAM START owner=$OWNER host=trinity-3-30 bytes=82012539 rate=4 read MB/s (pv -q -L 4m) src=$P/71f94277-362e-467c-a4bc-ccc9ae6b87c8.jsonl,$P/a97ad692-7041-4f72-8b75-8f8e29df8950.jsonl dest=/scratch/jjyeung/orch_n30/seal_plan/work/raw_*.jsonl (filtered parse)" >> $R
timeout 120 pv -q -L 4m $P/71f94277-362e-467c-a4bc-ccc9ae6b87c8.jsonl | python3 $W/extract.py $W/raw_71f94277.jsonl; r1=$?
timeout 60 pv -q -L 4m $P/a97ad692-7041-4f72-8b75-8f8e29df8950.jsonl | python3 $W/extract.py $W/raw_a97ad692.jsonl; r2=$?
END=$(date -u +%FT%TZ); ST2=$(date -u +%Y%m%dT%H%M%SZ)
echo "- $END STREAM ENDED owner=$OWNER host=trinity-3-30 bytes=82012539 read into parser (exit $r1,$r2; read-only, nothing written to NFS)" >> $R
echo "$END distillation lane seal_plan: hand stream $OWNER on trinity-3-30 ended (exit $r1,$r2); its STREAM ENDED line is in REGISTER.md." > $D/INBOX_TO_DISTILL_ORCH_${ST2}_seal_plan_hand_copy_ended.md
echo "- $END Distillation lane seal_plan: hand stream $OWNER on trinity-3-30 ended; STREAM ENDED line in REGISTER.md." >> /data3/jjyeung/mover_20261111/DISCUSSION.md
echo "done $r1 $r2"
