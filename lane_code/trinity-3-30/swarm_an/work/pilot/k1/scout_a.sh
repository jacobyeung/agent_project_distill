set -u
W=/scratch/jjyeung/orch_n30
echo "== host $(hostname -s) load $(cut -d' ' -f1-3 /proc/loadavg)"
echo "== geo_bakeoff_kit"; ls /scratch/jjyeung/geo_bakeoff_kit 2>&1 | head -40
echo "== geo_bakeoff_kit depth2 dirs"; find /scratch/jjyeung/geo_bakeoff_kit -maxdepth 2 -type d 2>/dev/null | head -60
echo "== CAPTURES.json"; find /scratch/jjyeung/geo_bakeoff_kit -maxdepth 4 -name 'CAPTURES.json' 2>/dev/null | head -10
echo "== sb_headacc2"; ls $W/sb_headacc2 2>&1 | head -30; echo "-- out"; ls $W/sb_headacc2/out 2>&1 | head -40
echo "== K1_ROWSETS"; find $W/sb_headacc2 -maxdepth 3 -name 'K1_ROWSETS*' 2>/dev/null | head
echo "== sb_k1list"; ls $W/sb_k1list 2>&1 | head; ls -la $W/sb_k1list/out 2>&1 | head -20
echo "== rasters"; for d in $W/gt_build/out/dose_pool/out/t1_gt/gt $W/gt_build/out/dose_pool/out/arkit_gt/gt $W/gt_build2/out/dose_pool/out/arkit_gt/gt; do echo "$d $(ls $d | wc -l)"; ls $d | head -3; done
echo "== sb_framepool out"; ls $W/sb_framepool/out 2>&1 | head -20; ls $W/sb_framepool/work 2>&1 | head -30
echo "== one raster"
f=$(ls $W/gt_build/out/dose_pool/out/t1_gt/gt/*.npz | head -1)
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python - "$f" <<'PY'
import sys, numpy as np
z = np.load(sys.argv[1], allow_pickle=True)
print(sys.argv[1])
for k in z.files:
    v = z[k]; print(' ', k, v.dtype, v.shape, (v.tolist() if v.size <= 40 and v.dtype.kind in 'USOib' else ''))
PY
