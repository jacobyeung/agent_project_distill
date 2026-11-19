set -u
W=/scratch/jjyeung/orch_n30
echo "== sb_ lanes"; ls -d $W/sb_* $W/so_* 2>/dev/null | tr '\n' ' '; echo
echo "== U2_REPORT"; head -c 2900 $W/sb_k1list/out/U2_REPORT.md; echo
echo "== u2.json top"; OMP_NUM_THREADS=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python - <<'PY'
import json
W='/scratch/jjyeung/orch_n30'
for fn in ['u2.json','u_union.json']:
    d = json.load(open(W+'/sb_k1list/out/'+fn))
    print(fn, type(d).__name__, (list(d.keys())[:20] if isinstance(d, dict) else len(d)))
    if isinstance(d, dict):
        for k, v in list(d.items())[:12]:
            s = json.dumps(v)[:300]; print('  ', k, type(v).__name__, (len(v) if hasattr(v,'__len__') else ''), s)
PY
echo "== FRAMEPOOL_REPORT"; head -c 2500 $W/sb_framepool/out/FRAMEPOOL_REPORT.md; echo
echo "== CAPTURES.tsv"; head -4 $W/sb_framepool/out/CAPTURES.tsv | cut -c1-500; wc -l $W/sb_framepool/out/CAPTURES.tsv
echo "== CAPTURE_MEMBERSHIPS.tsv"; head -4 $W/sb_framepool/out/CAPTURE_MEMBERSHIPS.tsv | cut -c1-500
echo "== frame_contract"; ls /scratch/jjyeung/geo_bakeoff_kit/data/frame_contract | head -20; ls /scratch/jjyeung/geo_bakeoff_kit/data/direct | head -20
echo "== headacc lanes"; for d in $W/sb_headacc*; do echo "-- $d"; ls $d | head -20; done 2>/dev/null
echo "== kit_k1a"; ls -d /scratch/jjyeung/*k1* $W/*k1* $W/*K1* 2>/dev/null | head -20
