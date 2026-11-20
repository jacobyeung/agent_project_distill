D=/project/community/jjyeung/okh7/a15_cot_ap39d650beda00a; cd $D
N=985f082abb9ff856/173486/cd89024cbaaac4b50/result.tar.gz
echo ==R; tar xzOf $N native/probe/54c1c9d606f2a398/FOV_RECEIPT.json
echo; echo ==P; tar xzOf $N native/probe/54c1c9d606f2a398/PHASE_COMPLETE.json
echo; echo ==C; cat /tmp/k1fwd2_canary.json
echo; echo ==END; TZ=UTC squeue -j 173486 -h -o '%T %M'
