set -eu
K=/project/community/jjyeung/okh7; ST=$K/813f42db/c21h544r; KIT=$ST-kit; SP=$K/ae71c903
test -s $ST/SCORES.json
test ! -e $ST/OTHER_H400.json
/usr/bin/python3 -B - <<'PY'
import json
K='/project/community/jjyeung/okh7'
for name,p in (('H400','a15_cot_apd7a6db629db02'),('H200','a15_cot_apdacd91c2f5c4b')):
    f=K+'/'+p+'/a/f/'
    d=dict(package=K+'/'+p,archive=f+'0.tgz',exit=f+'EXIT.json',receipt=f+'RETURN_RECEIPT.json')
    with open(K+'/813f42db/c21h544r/OTHER_%s.json'%name,'x') as o: json.dump(d,o,sort_keys=True,indent=2)
PY
cat > $ST/o_cmp.sh <<'EOS'
set -eu
K=/project/community/jjyeung/okh7; ST=$K/813f42db/c21h544r; KIT=$ST-kit
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
W=$(mktemp -d /tmp/c23cmpXXXXXX); echo WORK $W
cd $KIT
for o in H400 H200; do
  echo "== $(date -u +%TZ) vs $o"
  /usr/bin/python3 -B score_h_merge.py --spec $ST/SCORE_SPEC.json --other $ST/OTHER_$o.json --work $W/$o --out $ST/SCORES_vs_$o.json
  ls -la $ST/SCORES_vs_$o.json
done
du -sb $W
SP=$K/ae71c903
if grep -q ae71c903 $ST/SCORE_SPEC.json; then echo "POOL_REFERENCED: no move"; else
for R in dd982cd5c4b250002a564 dc863c3e6b41d0002a4ca; do
  if test -d $SP/$R && ! test -e ${SP}_fetched/$R; then mv $SP/$R ${SP}_fetched/$R && echo "moved $R"; else echo "not moved $R: $(ls -d $SP/$R ${SP}_fetched/$R 2>&1 | tr '\n' ' ')"; fi
done
fi
echo "== $(date -u +%TZ) DONE"
EOS
cd $ST && nohup setsid bash $ST/o_cmp.sh > $ST/cmp.log 2>&1 < /dev/null &
sleep 60; tail -c 2000 $ST/cmp.log
