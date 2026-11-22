#!/bin/bash
# refresh STATUS stamp, then wait up to 25 min for an ORCH event or inbox item
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; L=/scratch/jjyeung/orch_n30/lever10
t=$(date -u +%H%MZ)
sed -i -E "s/STATUS exact at [0-9]{4}Z/STATUS exact at $t/; s/as of [0-9]{4}Z/as of $t/" $L/STATUS.md
cp $L/STATUS.md $B/events/lever/STATUS.md
end=$(( $(date +%s) + 1500 ))
until ls $B/events/lever | awk '$0 > "20261122T1812Z"' | grep -q _ORCH_ || [ -n "$(ls $L/inbox)" ] || [ $(date +%s) -ge $end ]; do sleep 120; done
$L/work/poll.sh
