<!-- recovered by seal_plan: transcript=71f94277 line=1357 utc=2026-11-11T12:40:10.575Z kind=commands original_path=(bash command)  -->
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; cat > $S/restart_lane.sh <<'EOF'
#!/bin/bash
# restart_lane.sh <lane> <timeout-secs> [model]   Restart a Devin lane at a clean point under the recording launcher.
R=/scratch/jjyeung/orch_cd; n=$1; t=$2; m=${3:-claude-opus-5-5-high}; b=$R/$n/BRIEF.md
for p in $(pgrep -u jjyeung -f "^timeout [0-9]+ devin -p --prompt-file $b"); do kill -TERM -- -$p 2>/dev/null || kill -TERM $p; done
for i in 1 2 3 4 5 6; do pgrep -u jjyeung -f "devin -p --prompt-file $b" >/dev/null || break; sleep 1; done
if pgrep -u jjyeung -f "devin -p --prompt-file $b" >/dev/null; then echo "STILL ALIVE: $n"; exit 1; fi
grep -q '^## Restart note' $b || printf '\n## Restart note\nThis lane is restarted at clean points so that its session is recorded. If STATUS.md, work/ or events/ already hold work from an earlier session, read STATUS.md (its RESUME HERE block first) and continue from there; do not redo finished steps.\n' >> $b
bash $R/orch_tools/devin_bg.sh /home/jjyeung/agent_project_distill $b $m $t $R/$n/devin.out
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) orch-home-distill-79: restarted lane $n under the recording launcher (model $m, timeout $t s)." >> $R/ORCH_HANDOFF.md
EOF
chmod +x $S/restart_lane.sh; bash $S/restart_lane.sh vla_nav 36000