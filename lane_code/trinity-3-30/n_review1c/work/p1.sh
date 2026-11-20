W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
date -u +%TZ; tmux ls 2>/dev/null | grep -E 'tr17|tr15|tr16' 
ls -la $W/work/x24l3_back/ 2>/dev/null | head -20
ls -la $W/w24c/out/ | tail -30
ls -la $W/w24/work/build24k/ | grep -i -E 'report|log' | tail -20
ls -la /scratch/jjyeung/orch_n30/n_review/ | head -30
