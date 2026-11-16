# Runs on trinity-1-18 in tmux trr_yield: one listing per minute of the events folder; mirrors yield orders into the local root.
E=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/trin_read
Y=/scratch/jjyeung/orch_n30/trin_read/root/yield; mkdir -p $Y
while true; do for f in $(ls $E 2>/dev/null | grep -E '_ORCH_.*yield'); do [ -e $Y/$f ] || { cp $E/$f $Y/$f; echo "$(date -u +%FT%TZ) relayed $f"; }; done; sleep 60; done
