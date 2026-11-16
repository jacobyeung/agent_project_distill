G=/scratch/jjyeung/orch_n30/geo_k1; cd $G; date -u
ls harness/out_ref/captures | wc -l; for f in logs/ref_*.log; do tail -n1 $f; done
grep -c '"done"' logs/ref_*.log; grep -l "Traceback" logs/ref_*.log
if [ $(ls harness/out_ref/captures | wc -l) = 296 ]; then python3 k1towers/repro_cmp.py harness/out_ref/captures /scratch/jjyeung/orch_n30/e3_geom/work/harness/out/captures harness/REPRO_E3.json; fi
python3 -c "import json;m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'));c=m['captures'][0];print(c['dense_frames'][0]['path'])"
du -sh /scratch/jjyeung/k1/run_tower_sam_2 2>/dev/null
