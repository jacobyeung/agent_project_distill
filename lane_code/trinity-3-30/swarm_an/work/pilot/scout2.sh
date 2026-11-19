R=/scratch/jjyeung/orch_n30/trin_read/root
echo "== k6tk parts"; ls -la $R/k6tk/parts | head -8; ls -la $R/k6tk/MEMBERS.tsv.gz
zcat $R/k6tk/MEMBERS.tsv.gz | head -3 | cut -c1-300; zcat $R/k6tk/MEMBERS.tsv.gz | wc -l
zcat $R/k6tk/MEMBERS.tsv.gz | grep -m2 -E "5434c2265b166c943c3a67b94fcecce2ac913e7349f99409826c7cf959dc177f|7f8b99bfd9565ec8a1b8fad3450c21ee4f62be29c14b5118e55764b53bc739b0" | cut -c1-300
cat $R/STAGING.json 2>/dev/null | head -c 1500; echo
for d in m x cache needs t sj fsw; do echo "== $d"; ls $R/$d 2>/dev/null | head -12; done
echo "== sb_framepool"; ls /scratch/jjyeung/orch_n30/sb_framepool | head -20; ls /scratch/jjyeung/orch_n30/sb_framepool/work 2>/dev/null | head -30
echo "== gt_rasters"; ls /scratch/jjyeung/orch_n30/gt_rasters | head -20
echo "== trin_read/work"; ls /scratch/jjyeung/orch_n30/trin_read/work | head -30
