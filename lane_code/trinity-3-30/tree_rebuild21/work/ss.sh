# usage: bash ss.sh "<line>"  -> prepend running line, update header, copy to events
L=/scratch/jjyeung/orch_n30/tree_rebuild21; T=$(date -u +%FT%H:%MZ)
python3 $L/work/st.py "$T by tree_rebuild21 (Devin Opus high; session trinity-3-30 $L, work trinity-1-18 and 2-28; started 13:30Z; rotate by 19:00Z)" "- $(date -u +%H:%MZ) $1"
cp $L/STATUS.md /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/STATUS.md
