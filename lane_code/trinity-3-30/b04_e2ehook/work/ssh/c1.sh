date -u; tmux ls 2>&1 | grep -E 'b04|sl_'
D=/scratch/jjyeung/orch_n30/b04_e2ehook_sh; ls -la $D $D/harness/out 2>&1 | head -40; tail -15 $D/sh_run.log; cat $D/sh_run.start $D/sh_run.end 2>&1
L=/scratch/jjyeung/orch_n30/b04_e2ehook_sl; ls -la $L $L/full $L/emb 2>&1 | head -40; tail -5 $L/full.log; tail -10 $L/emb.log; grep -c '"rows"' $L/full.log
uptime; df -h /scratch | tail -1
