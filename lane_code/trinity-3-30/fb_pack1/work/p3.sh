R=/scratch/jjyeung/orch_n30; cd $R/sb_fullinv
/scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json
d=json.load(open('out/FULL_INVENTORY.json'))
fh=d['frame_host']
for k in ['kit_settings','recorded_P_frame_archives','recorded_P_frame_audits','required_store_databases']:
    print('##',k); print(json.dumps(fh[k],indent=0)[:3000])
for k in ['frame_map','frame_plan']:
    print('##',k); print(json.dumps(fh['metadata'][k],indent=0)[:1500])
print('## camera_requests', fh['camera_requests'])
print('## top keys', list(d.keys()))
PY
echo; head -c 600 work/frames/units.json; echo; ls work/frames
