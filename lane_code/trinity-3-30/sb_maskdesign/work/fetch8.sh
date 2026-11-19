K=/scratch/jjyeung/orch_n30/sb_kbox4
echo "=== serving_reference 1-100"; sed -n '1,100p' $K/serving_reference.py | cut -c1-330
echo "=== predicted.py"; sed -n '1,80p' $K/predicted.py | cut -c1-330
echo "=== run.sh"; cat $K/run.sh; echo "=== maskfail run.sh"; cat /scratch/jjyeung/orch_n30/sb_maskfail/run.sh
echo "=== variantlib 1-30"; sed -n '1,30p' /scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/vendor_sam/variantlib.py | cut -c1-1800
