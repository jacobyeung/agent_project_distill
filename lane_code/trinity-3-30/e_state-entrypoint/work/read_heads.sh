#!/bin/bash
# reads first 30 lines of each .md record once, <=30 files/min
D=/data2/jjyeung/agent_project_data/distill_design
W=/scratch/jjyeung/orch_n30/e_state-entrypoint
grep '\.md$' $W/ref/design_ls.txt | grep -vx INDEX.md | while read f; do
  [ -s "$W/ref/heads/$f" ] && continue
  head -n 30 "$D/$f" > "$W/ref/heads/$f"
  sleep 2.1
done
echo DONE > $W/ref/heads.DONE
