"""Run the native full H1 first-step fixture on every rank, without collectives."""
import argparse
import runpy
import sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--world',type=int,choices=[4],default=4);p.add_argument('--output',default='logs/h1_first_step.json');p.add_argument('--force-pose-own',action='store_true');a=p.parse_args()
K=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(K));sys.argv=[str(K/'tests/first_step.py'),'--tree',str(K/'tree'),'--out',a.output,'--h1']+(['--force-pose-own'] if a.force_pose_own else [])
runpy.run_path(str(K/'tests/first_step.py'),run_name='__main__')
