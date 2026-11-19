set -u
R=/scratch/jjyeung/orch_n30; mkdir -p $R/fb_pack; date -u +%FT%TZ; df -h /scratch | tail -1
echo "== orch_n30"; ls $R | tr '\n' ' '; echo
echo "== jjyeung"; ls /scratch/jjyeung | tr '\n' ' '; echo
echo "== sb_fullinv"; ls $R/sb_fullinv $R/sb_fullinv/out $R/sb_fullinv/work 2>&1 | head -60
for d in sb_rowC sb_rowC2 sb_rowC3 sb_rowF sb_fhalias2 sb_phfix; do echo "== $d/out"; ls -la $R/$d/out 2>&1 | head -25; done
echo "== W w24"; ls $R/tree_rebuild10_w/w24/out $R/tree_rebuild10_w/w24/work 2>&1 | head -60
