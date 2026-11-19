R=/scratch/jjyeung/orch_n30
date -u +%TZ
python3 - <<'PY'
import json,re
for f in ['/scratch/jjyeung/orch_n30/sb_ktow3/out/GPU_NEED.json','/scratch/jjyeung/orch_n30/sb_rkdocs/out/GPU_NEED.json']:
    try: s=open(f).read()
    except Exception as e: print(f,e); continue
    paths=sorted(set(re.findall(r'/scratch/jjyeung/[A-Za-z0-9_./-]+',s)))
    print(f, len(s)); [print('  ',p) for p in paths[:40]]
PY
for d in /scratch/jjyeung/k1_frames /scratch/jjyeung/k1/run_tower_sam_2 /scratch/jjyeung/k1/run_convert_2 /scratch/jjyeung/envs/sam3_capretry_native_v1 /scratch/jjyeung/envs/p1cpu /scratch/jjyeung/n13_outage/sam3_ckpt; do timeout 60 du -sh $d 2>/dev/null; done
ls /scratch/jjyeung/envs | tr "\n" " "
