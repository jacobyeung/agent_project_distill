<!-- recovered by seal_plan: transcript=71f94277 line=27476 utc=2026-11-14T01:53:20.445Z kind=commands original_path=(bash command)  -->
N=$(date -u +%Y%m%dT%H%MZ); C=/scratch/jjyeung/orch_cd; cat > $C/evalx/inbox/${N}_ORCH_RULING_camera_baseline_hardware_evidence.md <<'EOF'
# ORCH ruling: how to close the camera baselines' hardware gap

Both baseline jobs (169051, 169063) ran on `orchard-community-2` and their GPU UUIDs are retained. The model is admitted as established if either holds:

1. the UUID appears in any authenticated record that names the model (for example the production job's rank records on that node, or one of your own hardware records), or
2. the node's own description shows a single GPU type: one line of `scontrol show node orchard-community-2` (its `Gres` and `CfgTRES`) in your next routine session, with the raw line saved.

If the node carries one GPU type, every card on it is that type and the mapping is closed for both jobs. Record which rule closed it. Until then keep the label as you have it. This is a reporting gate only; camera types are judged by the routed read.

Noted: step-200 job 169367 is pending; same wait policy as for step 100 (no resubmission; a QUESTION with Slurm's start estimate if it is still pending 45 minutes after submission).
EOF
T=$(date -u +%Y-%m-%dT%H:%M:%SZ); echo "$T orch-home-distill-79: evalx RESULT 0150Z: STEP-200 direct read submitted once as job 169367 (token bffa0d6ef; producer 8365bd3b; reader fb2796c5; launcher digest b13c6dcc); PENDING at 01:49Z (nodes down, drained or reserved). Camera baseline jobs 169051 / 169063 on orchard-community-2: UUIDs retained, model mapping missing from accounting. RULING ($N): mapping closes if the UUID appears in an authenticated record naming the model, or if scontrol shows a single GPU type on that node (next routine session). Re-armed evwait (bckunuajl)." >> $C/ORCH_HANDOFF.md; echo $N