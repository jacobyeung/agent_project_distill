W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24h/out/kit_n_go
date -u +%TZ
echo "== z.py defs"; grep -n "^def \|^    def " $K/b/z.py | head -60
echo "== z 200-240"; sed -n 200,240p $K/b/z.py
echo "== z 370-400"; sed -n 370,400p $K/b/z.py
echo "== callers of z functions in job.sh/J"; grep -n "z\.\|from z import\|b/z.py\| z " $K/job.sh $K/b/*.py $K/b/*.sh 2>/dev/null | grep -v "^$K/b/z.py" | head -40
echo "== ARM usage"; sha256sum $W/w24h/out/arm_routing.py $W/w24h/out/ARM_ROUTING_USAGE.md; cat $W/w24h/out/ARM_ROUTING_USAGE.md
echo "== rdiff"; ls -la $W/work/sel24/ 2>/dev/null | head; sha256sum $W/work/sel24/*/rdiff.py $W/work/sel24/rdiff.py 2>/dev/null
