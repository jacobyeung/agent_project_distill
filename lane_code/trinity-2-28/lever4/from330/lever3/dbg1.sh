C=/scratch/jjyeung/orch_n30/lever1_c; R=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs
for f in r1bootrev r4boot2rev r4bootrev; do echo "== $f"; cat $C/${f}_run.log | tail -c 600; ls -la $C/$f 2>&1 | head; done
ls -t $R | head -8
tmux capture-pane -p -t l3_r4boot2rev | tail -15
ps -ef | grep -c "[c]odex"
