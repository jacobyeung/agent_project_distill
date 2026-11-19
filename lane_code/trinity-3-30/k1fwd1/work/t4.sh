K=/scratch/jjyeung/orch_n30/k1_ops3/work/partb/build7
cd $K; ls | tail -n +40; ls job 2>/dev/null
f=$(ls -d job/stage_job.py */stage_job.py 2>/dev/null | head -3); echo "STAGE=$f"
for s in $f; do wc -l $s; grep -n "export\|parts\|def \|gcloud\|cat \|/tmp\|destination\|heads\|artifact" $s | cut -c1-200 | head -120; done
cat build_package.py | head -150
