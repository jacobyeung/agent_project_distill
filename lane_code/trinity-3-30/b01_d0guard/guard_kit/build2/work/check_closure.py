from pathlib import Path
import sys,os,json
B=Path(__file__).resolve().parents[1];W=B.parents[1]/'work';T=W/'from113/work/tree'
sys.path[:0]=[str(B/'out/guard_kit'),str(W/'from113/work/np226'),str(W/'from113/work/pyextra'),str(T)]
from student_pilot import carrier_c1_run as trainer
import closure
from guard_core import write
source=W/'d0closure/closure_359fcc3c.tar'
if closure.sha(source)!='41bb90d0418ab37715ae66358e875cb4f337f7a63349df4d96498c6452cda964':raise ValueError('Supplied closure tar hash differs')
r=closure.pack(source,B/'out/candidate_m50',50,trainer,W/'from113/work/obj/m544_artifact.json')
write(B/'out/CLOSURE_ADMISSION.json',r['admission']);print(json.dumps(r['admission'],indent=2))
