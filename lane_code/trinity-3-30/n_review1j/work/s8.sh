T=/scratch/jjyeung/orch_n30/n_review/r1j/t; R=/scratch/jjyeung/orch_n30/n_review/r1j/div
cd $T && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import sys,json,glob; sys.path.insert(0,'.')
R='/scratch/jjyeung/orch_n30/n_review/r1j/div'
from pathlib import Path
import student_pilot.r1_persisted as rp
local={Path(f).name:f for f in glob.glob(R+'/*')}
rp.relocated=lambda pin: local.get(pin['sha256'], pin['path'])
from student_pilot import carrier_c1_run as c, c1_pose_mix as m
pose={'path':'/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f02f16ad/s/a3v2/division.json','sha256':'f41d15aadd7e0bde758a14806073424af2c3c70997efb8a0ce88226ace151ea5'}
vqa={'path':'/scratch/jjyeung/orch_n30/tree_rebuild_w/w12/work/n1fix2/inputs/0d28fdd432b0.json','sha256':'0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad'}
lus={'path':'/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/e84d901c/z/4c230a7e.json','sha256':vqa['sha256']}
print('pointing/routing (pin == pose pin):', c.division_admits(dict(pose), pose))
print('vqa as receipted (trinity path):', c.division_admits(vqa, pose))
print('vqa with the path a3v2 names for its parent:', c.division_admits(lus, pose))
print('ancestor_admits(pose, vqa):', m.ancestor_admits(pose, vqa), ' (pose, lustre):', m.ancestor_admits(pose, lus))
PY
