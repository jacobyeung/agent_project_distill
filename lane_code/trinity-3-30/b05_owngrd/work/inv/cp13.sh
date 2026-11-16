cd /scratch/jjyeung/n30_mirror
ls -la gt_build gt_build2
for f in gt_build/K1_GT_RASTERS_259.tar gt_build2/K1_GT_RASTERS_GTB2_37.tar; do
  b=$(basename $f)
  cat $f | ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-3-30.ib "cat > /scratch/jjyeung/orch_n30/b05_owngrd/work/gt/$b"
  sha256sum $f
done
