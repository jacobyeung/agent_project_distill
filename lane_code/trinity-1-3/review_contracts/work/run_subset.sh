L=/scratch/jjyeung/orch_n30/review_contracts/work
FILES=$(tail -n 1 $L/subset.txt)
for t in base patched; do
  export OUTD=$L/tmp/sub3_$t; mkdir -p $OUTD
  bash $L/runpt2.sh $L/trees/$t $FILES --continue-on-collection-errors --junitxml=$L/logs/sub_$t.xml > $L/logs/sub_$t.log 2>&1
done
echo done > $L/logs/sub_done
