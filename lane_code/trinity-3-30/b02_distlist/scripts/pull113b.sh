cd /scratch/jjyeung/orch_n30/native_r2/work/obj || exit 1
tar xOf masks_4984fac22d84e8c5.tar sj/mask_recall_run/kit/out/ITEMS.jsonl > /dev/null || exit 1
tar cf - --null -T /dev/null >/dev/null
python3 - <<'PY'
import tarfile, sys
want={'sj/mask_recall_run/kit/out/ITEMS.jsonl','sj/mask_recall_run/results/dense_aliases/MANIFEST.json','sj/mask_recall_run/results/dense/MANIFEST.json','sj/orch_cd/evalx/work/milestone/actual_cache_cpu/MASK_CACHE.json'}
src=tarfile.open('masks_4984fac22d84e8c5.tar')
with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as out:
    for m in src.getmembers():
        if m.name in want:
            out.addfile(m, src.extractfile(m))
    g=tarfile.open('geometry_8c58df1547371bdb.tar')
    for m in g.getmembers():
        if m.name.endswith('.json') and m.size < 100000:
            out.addfile(m, g.extractfile(m))
PY
