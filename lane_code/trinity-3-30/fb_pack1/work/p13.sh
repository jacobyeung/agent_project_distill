B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30; F=/scratch/jjyeung/orch_n30/fb_pack
date -u +%TZ
timeout 300 bash $B/tools/ossh.sh 'tar --seek -tf /project/community/jjyeung/distill/okit/in/cr/rb_61aebb2b2fca.tar' < /dev/null > $F/in/f14_members.txt 2>$F/in/f14_members.err; date -u +%TZ; wc -l $F/in/f14_members.txt; head -3 $F/in/f14_members.txt; grep -v "^@\|WARN\|Someone\|IT IS\|It is\|finger\|SHA256\|Please\|Add\|Offend\|disabled" $F/in/f14_members.err | head -3
cd $F && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'PY'
import json,gzip,re
mem=set(re.findall(r'([0-9a-f]{64})\.png',open('in/f14_members.txt').read()))
print('f14 png members',len(mem))
m={}
for l in gzip.open('in/pk/frame_map.jsonl.gz','rt'):
    r=json.loads(l); m[(r['d'],r['s'],r['i'])]=r['sha256']
d=json.load(open('/scratch/jjyeung/orch_n30/sb_fullinv/work/frames/camera_wording.json'))
allsh=set(); diff=set(); rows_diff=set()
for r in d['rows']:
    dd,ss=r['scene_token'].split('/',1)
    for i,f in zip(r['indices'],r['frames']):
        allsh.add(f['sha256'])
        if m.get((dd,ss,i))!=f['sha256']: diff.add(f['sha256']); rows_diff.add(r['qid'])
print('camera unique shas',len(allsh),'in f14',len(allsh&mem),'differing-from-k6tk unique',len(diff),'of which in f14',len(diff&mem),'rows citing differing',len(rows_diff))
json.dump(dict(f14_members=len(mem),camera_unique=len(allsh),camera_in_f14=len(allsh&mem),diff_unique=sorted(diff),diff_in_f14=len(diff&mem),rows_citing_diff=sorted(rows_diff)),open('CAMERA_F14_CHECK.json','w'))
PY
