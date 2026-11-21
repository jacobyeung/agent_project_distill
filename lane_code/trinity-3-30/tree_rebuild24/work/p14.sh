W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; tmux ls | grep tr2; E3=$W/w24z9/out/e3; head -30 $E3/trinity.sh; grep -n -i "trinity" $E3/E3_USAGE.md | head -10 | cut -c1-300
O=$W/work/e3t_900003; test -e $O && { echo EXISTS; exit 1; }
timeout 900 nice -n 10 bash $E3/trinity.sh 900003 /scratch/jjyeung/orch_n30/n_ops8_x/sess_900003.json $O; echo rc=$?
M='s#https?://[^ "]*#[URL]#g'; ls $O; F=$(ls $O/E3.json $O/*/E3.json 2>/dev/null | head -1); echo F=$F; sed -E "$M" $F | head -120
