"""Exact camera materialization identity, shared with S1 preparation."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tree'))
from student_pilot.h1_faithful import identity_check as check, identity_rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rows');a=p.parse_args()
    print(json.dumps(check(identity_rows(a.rows)),indent=2))
