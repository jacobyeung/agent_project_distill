#!/bin/bash
set -u
B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; P=/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/swarm_opt/work/prompts
R=/scratch/jjyeung/orch_n30/so_rv_tick2
if [[ ! -d $R ]]; then mkdir -p $R && cp $P/tick2.sh.copy $R/tick.sh && cp $P/so_rv_tick2.md $R/PROMPT.md && sha256sum $R/tick.sh > $R/SHA256
  cp /scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs/20261119T062938Z_so_rv_tick/final_message.md $R/REVIEW1.md
  cp $B/events/swarm_opt/20261119T0615Z_ORCH_NOTE_tick_tweaks.md $R/ORCH_NOTE.md
  tmux new-session -d -s so_rv_tick2 "cd $R && nice -n 10 bash $B/tools/codex_local.sh review $R $R/PROMPT.md --model gpt-6-astra --effort high --label so_rv_tick2 --skip-git-check > $R/dispatch.log 2>&1"; echo "started so_rv_tick2"; fi
bash $P/poll118.sh
