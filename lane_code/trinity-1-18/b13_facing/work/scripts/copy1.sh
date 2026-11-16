cd /scratch/jjyeung/orch_n30
du -sh rows_rebuild3/out/rows/d0_v5/vqa rows_rebuild3/work/validator rows_rebuild/work/d0 2>&1
ls rows_rebuild/work/d0 | head -50
tar cf - --exclude='readk/evidence/chain_*' --exclude='readk/evidence/bind_*' --exclude='readk/evidence/SOURCE.patch' cont_ops/work/d0/readk evalx27/work/pull/x27/res/e193/merged/away evalx27/work/pull/x27/res/e193/merged/forward rows_rebuild3/out/rows/d0_v5/vqa rows_rebuild3/work/validator rows_rebuild3/out/rows/d0_v5/FAMILY_TYPE_COUNTS.json rows_rebuild3/out/rows/d0_v5/REMOVED_ROWS.jsonl | ssh -o ConnectTimeout=20 trinity-1-18.ib "cd /scratch/jjyeung/orch_n30/b13_facing/work/in/t13 && tar xf -"
echo rc=$?
