R=/scratch/jjyeung/orch_n30/n_review/r1d
for f in a ep i pl rd rg z; do echo "######## $f"; cat $R/diff_$f.txt; done
echo "######## rb"; head -120 $R/diff_rb.txt
