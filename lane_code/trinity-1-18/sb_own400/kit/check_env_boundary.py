"""Verify the reported boundary and its predecessor with the unchanged scorer."""
import os,sys
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='8'
os.environ['CUDA_VISIBLE_DEVICES']='';sys.dont_write_bytecode=True
from core import *
from score_400 import module,S1,summarize,choose
import numpy as np

def main():
 s=module(S1,'verify_env');bars=read(ROOT/'out/BARS_FROZEN.json');base=ROOT/'out/env_sensitivity_b'
 meta=read(base/'PAIR_INPUTS.json');checked(base/'pairs.npz',meta['pairs_sha256']);res=read(base/'ENV_SENSITIVITY.json');records=[]
 with np.load(base/'pairs.npz') as z:
  for room,cap,lo,hi in meta['records']:records.append({'room':room,'gt':z['gt'][lo:hi],'pred':{'A':z['pred'][lo:hi]}})
 v=res['smallest_increase']['multiplier'];answers=[]
 for m in [1.,np.nextafter(v,1.),v]:
  for r in records:r['pred']['B']=r['pred']['A']*m
  reports=[summarize(s,[r for r in records if r['room'] in f['test_rooms']]) for f in bars['folds']]+[summarize(s,records)]
  answers.append({'multiplier':m,'chosen_donor':choose(reports[:2],reports[2]),'B-A':[r['B-A'] for r in reports]})
 assert [x['chosen_donor'] for x in answers]==[400,400,544]
 atomic(ROOT/'out/ENV_BOUNDARY_CHECK_FINAL_B.json',{'input_sha256':{str(p):sha(p) for p in [base/'ENV_SENSITIVITY.json',base/'PAIR_INPUTS.json',base/'pairs.npz',ROOT/'out/BARS_FROZEN.json',KIT/'score_400.py',pathlib.Path(__file__),S1]},'checks':answers,'command':'nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B kit/check_env_boundary.py'})
if __name__=='__main__':main()
