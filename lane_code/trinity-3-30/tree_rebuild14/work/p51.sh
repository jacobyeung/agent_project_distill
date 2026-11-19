W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; S=/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j; mkdir -p $S/out
cd $W/w24 && cp -a out/kit_n_go $S/out/ && cp out/*.md out/UPLOADS_*.json $S/out/ 2>/dev/null
d=$(ls -dt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/*tree_rebuild_qadmit | head -1); cp $d/final_message.md $S/qadmit.md
python3 -B - <<'PY'
import json,glob,os,shutil
S='/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24j'; os.makedirs(S+'/staged',exist_ok=True); n=0
for f in glob.glob('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/UPLOADS_*.json'):
  d=json.load(open(f)); items=d if isinstance(d,list) else d.get('files') or d.get('entries') or []
  for e in items:
    if isinstance(e,dict) and 'ca0616db' in json.dumps(e) and e.get('local_path') and os.path.isfile(e['local_path']):
      shutil.copyfile(e['local_path'],S+'/staged/'+os.path.basename(e.get('name',e['local_path']))); n+=1
print('staged ca0616db files',n)
PY
mkdir -p $S/work && cp -a $W/w24/work/tree_r1 $S/work/tree_r1 && cp -a $W/w24/work/tree_r1 $S/work/tree_r1_base
du -s --block-size=1M $S; ls $S $S/staged
cd $S && tar cf - . | timeout 600 ssh -o ConnectTimeout=20 -o BatchMode=yes trinity-2-28.ib 'mkdir -p /scratch/jjyeung/orch_n30/tree_rebuild14_w24j && cd /scratch/jjyeung/orch_n30/tree_rebuild14_w24j && tar xf - && du -s --block-size=1M . && ls'
