W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; L=$W/w19; date -u +%TZ; tmux ls | grep tr11; tail -c 300 $W/work/rev19_dispatch.log
ls $L/work/build19/kits $L/work/build19/proofs | head -60
for d in $L/work/build19/kits/*/; do echo "== $d"; ls -la $d | head -25; done 2>/dev/null | head -90
ls $L/work/build17/proofs/operator 2>/dev/null | head; ls $L/work/build18/proofs 2>/dev/null | head -30
