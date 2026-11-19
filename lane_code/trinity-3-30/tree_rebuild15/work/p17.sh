O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out; K=$O/kit_n_go/b; date -u +%TZ
cat $K/rg.py | cut -c1-300
echo "==== z.py bootstrap"; grep -n -E "def bootstrap|Q_MODE|a\.py|'r'|/tmp/q_22c714e1|--bind|ns ?=|p2|'/p'" $K/z.py | head -40 | cut -c1-300
echo "==== begin_host"; X=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1; grep -n "def begin_host" -A 25 $X/launch_r1/entry.py | cut -c1-250
ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf24k/pkg/work/build24k | head; ls /scratch/jjyeung/orch_n30/tree_rebuild10_w/work/conf24k/pkg/out | head -30 | tr '\n' ' '
