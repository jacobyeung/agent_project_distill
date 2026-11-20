#!/bin/bash
# fetch_one.sh ID OUTDIR : one tar stream of the 32 selected depth PNGs, pincams, traj and annotation of one ARKit capture
set -euo pipefail
ID=$1; W=$2; A=/data3/shared/datasets/arkitscenes/3dod/Training/$ID; mkdir -p $W/src
ls $A/${ID}_frames/lowres_depth > $W/depth_list.txt
FI=$(python3 -c "import json;r=json.load(open('/scratch/jjyeung/orch_n30/gt_rasters/work/LOCAL_PINNED_79.json'));print(json.dumps([x['grid'] for x in r if x['canonical']=='arkitscenes/$ID'][0]))")
python3 - "$W" "$ID" "$FI" <<'PY'
import json,sys
W,ID,FI=sys.argv[1],sys.argv[2],json.loads(sys.argv[3])
ts=lambda s: float(s.split('_')[1].rsplit('.',1)[0])
d=sorted(open(W+'/depth_list.txt').read().split(),key=ts)
f=[f'{ID}_3dod_annotation.json',f'{ID}_frames/lowres_wide.traj']+[f'{ID}_frames/lowres_depth/'+d[i] for i in FI]+[f'{ID}_frames/lowres_wide_intrinsics/'+d[i][:-4]+'.pincam' for i in FI]
open(W+'/files.txt','w').write('\n'.join(f)+'\n')
PY
tar cf - -C $A -T $W/files.txt | tar xf - -C $W/src
echo "$FI" > $W/frame_indices.json
