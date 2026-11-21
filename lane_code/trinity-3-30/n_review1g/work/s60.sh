W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; K=$W/w24z7/out/kit_n_go
date -u +%TZ; sha256sum $K/b/z.py $K/b/o.py $K/b/pc.py $K/b/pc.sh
sed -n 570,585p $K/b/z.py | cut -c1-250
grep -n 'Q_ROOT' $K/b/*.py $K/b/*.sh 2>/dev/null | head -12 | cut -c1-250
grep -n 'o.py\|exit_status\|rooms' $K/b/pc.py | head -12 | cut -c1-250
sed -n 1,14p $K/b/o.py | cut -c1-250
ls $W | grep -i 'w24z8\|w24z10' ; ls $W/w24z8b/out 2>/dev/null | head -20
