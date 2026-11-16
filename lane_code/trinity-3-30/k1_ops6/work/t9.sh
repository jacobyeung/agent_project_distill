N=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $N
sed -n '/"depth_init"/,$p' evidence/B7_DEPTH_MAPPED.log
R=$(cat evidence/B7_NS.run)
echo "=== bootstrap_failure.log"; tail -c 3000 $R/success/bootstrap_failure.log
echo "=== batch.log"; tail -c 2000 $R/success/batch.log
