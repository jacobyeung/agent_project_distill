from pathlib import Path
import argparse,sys
B=Path(__file__).resolve().parents[1];W=B.parents[1]/'work'
sys.path[:0]=[str(B/'out/guard_kit'),str(W/'from113/work/np226'),str(W/'from113/work/pyextra'),str(W/'from113/work/tree')]
from student_pilot import carrier_c1_run as trainer
from closure import pack
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--step',type=int,required=True);a=p.parse_args()
pack(a.source,a.out,a.step,trainer,W/'from113/work/obj/m544_artifact.json')
