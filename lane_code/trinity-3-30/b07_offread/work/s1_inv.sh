cd /scratch/jjyeung/orch_n30 || exit 1
echo "== evalx27/work"; ls evalx27/work 2>&1 | head -50
echo "== kit"; ls -la evalx27/work/kit 2>&1 | head -60
echo "== kit_revsi"; ls -la evalx27/work/kit_revsi 2>&1 | head -60
du -sh evalx27/work/kit evalx27/work/kit_revsi 2>&1
du -sh evalx27/work/kit/* evalx27/work/kit_revsi/* 2>&1 | sort -h | tail -30
echo "== readk"; ls -la cont_ops/work/d0/readk 2>&1 | head -40; du -sh cont_ops/work/d0/readk 2>&1
df -h /scratch | tail -1
