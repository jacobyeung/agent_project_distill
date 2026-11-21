W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z12/out/kit_n_go; T=/scratch/jjyeung/orch_n30/n_review/r1f/tcpx
date -u +%TZ
wc -c $K/b/*.py $K/b/*.sh $K/job.sh < /dev/null | sort -n | tail -40
echo "== rv.py"; cat -n $K/b/rv.py < /dev/null
echo "== ep.py"; cat -n $K/b/ep.py < /dev/null | head -80
echo "== job.sh"; cat -n $K/job.sh < /dev/null | head -60
