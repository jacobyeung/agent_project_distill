W=/scratch/jjyeung/orch_n30/tree_rebuild10_w
cd $W || exit 1
L=$(ls -d w24z11b/out/*.py w24z11b/out/*.sh w24z11b/out/*.md w24z12/out/*.py w24z12/out/*.sh w24z12/out/*.md w27fix/src/* w28fix/src/* 2>/dev/null | while read f; do [ -f "$f" ] && [ $(stat -c %s "$f") -lt 3000000 ] && echo "$f"; done)
echo "$L" | wc -l
du -ch $L | tail -1
ls -la w24z12/out | head -60
ls w24z12/work | head -60
tar cf - $L | ssh -o ConnectTimeout=20 trinity-3-30.ib 'cd /scratch/jjyeung/orch_n30/tree_rebuild28/work/fix8/src && tar xf -' && echo COPIED
