#!/bin/bash
# usage: push.sh <local tar> <remote name under W>
W=/project/community/jjyeung/okh7/e6fc152498
/usr/bin/python3 -s /scratch/jjyeung/io_governor/gated_reader.py "$1" | /usr/bin/python3 -s /scratch/jjyeung/io_governor/ratelimit.py -q -L 1000 -B 65536 | timeout 7200 bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/ossh.sh "cat > $W/$2.partial"
echo "rc=${PIPESTATUS[*]} $(date -u +%FT%TZ)"
