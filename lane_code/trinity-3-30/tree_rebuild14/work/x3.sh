J=/scratch/jjyeung/orch_n30/tree_rebuild14_w24j; date -u +%TZ; cat $J/out/BUILD24J_REPORT.md; echo; cat $J/out/ROUTING_SELECTION_PIN.json | head -c 800; echo
cd $J && tar cf - out work/tree_r1 work/tree_r1_base | timeout 300 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-1-18.ib 'mkdir -p /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j_back && cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j_back && tar xf - && du -s --block-size=1M . && sha256sum out/tree_rebuild_b24j_*.tar | cut -c1-16'
sha256sum $J/out/tree_rebuild_b24j_*.tar | cut -c1-16
