set -u
W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
echo "## host $(hostname -s) $(date -u +%FT%TZ)"; free -g | head -2; df -h /scratch | tail -1; nproc
tmux ls 2>&1 | cut -c1-80
which agent cursor-agent codex 2>&1; ls ~/.local/bin 2>/dev/null | head -30
L=/scratch/jjyeung/orch_n30/codex_local/agent/scratch/codex_runs; ls $L 2>/dev/null | tail -5; tail -3 $L/CODEX_SPEND.log 2>/dev/null
echo "## kit meta"; ls -la $W/w12/fixtures/work/kit07ca49df_meta/m/k/ 2>&1 | head -40
echo "## w19"; cat $W/w19/work/build19/STATUS.md 2>&1 | head -20
echo "## registry"; ls $W/w19 2>&1 | head; ls /scratch/jjyeung/n30_mirror/ 2>&1; ls /scratch/jjyeung/n30_mirror/rows_a2 2>&1 | head -30
echo "## evidence gap files"; ls $W/w19/*/inputs 2>/dev/null | head; 
for f in $(ls -d $W/w19/n1fix2/inputs 2>/dev/null); do ls $f | head -40; done
