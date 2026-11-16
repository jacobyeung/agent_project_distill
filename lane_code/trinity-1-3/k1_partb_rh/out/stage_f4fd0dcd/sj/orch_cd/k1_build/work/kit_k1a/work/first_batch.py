"""Run rs_tree's real membership/frame admission on each rank's first batch."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
sys.path.insert(0,str(gate.ROOT/'rs_tree/work/tree_r1'))
from student_pilot.r1_contract import Admission
def check(rows,contract):
 admission=Admission(contract)
 for row in rows:admission.check(row,require_frames=True)
 return len(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--rows',required=True);p.add_argument('--contract',required=True);p.add_argument('--out',required=True);p.add_argument('--rank',type=int,required=True);a=p.parse_args()
 count=check([json.loads(l) for l in open(a.rows)],json.loads(Path(a.contract).read_text()))
 Path(a.out).write_text(json.dumps(dict(status='PASS',rank=a.rank,rows=count,rows_sha256=gate.sha(a.rows),contract_sha256=gate.sha(a.contract)))+'\n')
if __name__=='__main__':main()
