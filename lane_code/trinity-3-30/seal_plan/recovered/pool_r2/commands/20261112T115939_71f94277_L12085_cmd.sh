<!-- recovered by seal_plan: transcript=71f94277 line=12085 utc=2026-11-12T11:59:39.838Z kind=commands original_path=(bash command)  -->
cd /scratch/jjyeung/orch_cd/pool_r2/work/r2; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -c "
import json;from pathlib import Path
r=json.load(open('SHM_RASTERS_REQUIRED.json'));import os
t=sum(os.path.getsize(x['source']) for x in r if os.path.exists(x['source']));m=[x['source'] for x in r if not os.path.exists(x['source'])]
print(len(r),'rasters',t,'bytes; missing sources',len(m))"; ls | head -20; grep -l -i "raster" *.py 2>/dev/null | head; grep -n -i -E "pending_validation|stage_rasters|after staging|then run" ../../out/r2/TOTALCOUNT/MANIFEST.md ../../out/r2/TOTALCOUNT/*.md 2>/dev/null | cut -c1-260 | head -8