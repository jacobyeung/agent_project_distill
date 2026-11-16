set -u
echo "host=$(hostname -s) $(date -u +%FT%TZ)"
W=/scratch/jjyeung/orch_n30/native_r2/work
[ -d $W ] || { echo "MISSING $W"; exit 0; }
echo "== $W $(timeout 60 find $W -type f 2>/dev/null | wc -l) files"
timeout 120 find $W \( -iname 'MODELS*.json' -o -name 'setlib*.py' -o -iname '*.pkl' -o -iname '*.joblib' -o -iname 'requirements*' -o -iname '*sklearn*' -o -iname 'kit_combo*.tar*' -o -iname 'mask_recall_kit*' -o -iname 'P2_RESULT.json' -o -iname 'PROOFS.md' \) -not -path '*/site-packages/*' -type f -printf '%s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | head -100 > /tmp/jjyeung_rk1_113.txt
cat /tmp/jjyeung_rk1_113.txt
echo "== sha256"
awk '$1<20000000{print $3}' /tmp/jjyeung_rk1_113.txt | xargs -r -d '\n' sha256sum
echo "== py files naming sklearn (bounded to $W, excluding site-packages)"
timeout 120 find $W -name '*.py' -not -path '*/site-packages/*' -size -2M -print0 2>/dev/null | xargs -0 -r grep -l -E 'sklearn|scikit' 2>/dev/null | head -20
echo "== sklearn dist-info in runtimes under $W"
timeout 60 find $W -maxdepth 7 -type d -iname 'scikit_learn-*.dist-info' 2>/dev/null | head
echo "== envs"
for p in /scratch/jjyeung/envs/*/bin/python; do [ -x "$p" ] && echo "$p $(timeout 30 $p -c 'import sklearn;print(sklearn.__version__)' 2>&1 | tail -1)"; done
