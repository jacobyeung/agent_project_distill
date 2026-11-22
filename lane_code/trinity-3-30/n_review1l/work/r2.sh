J=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14
sed -n 1,100p $J/out/admit_test.py
echo ====; ls $J; ls $J/out; ls $J/work | head -30; du -sh $J/work/tree_r1c 2>/dev/null; cat $J/out/TREE_SEAL.json 2>/dev/null | head -c 600
df -h /scratch | tail -1
