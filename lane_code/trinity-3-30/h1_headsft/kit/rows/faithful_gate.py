"""Refuse S1 below 95% camera identity on rows or a SQLite receipt (CPU only)."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tree'))
from student_pilot.h1_faithful import identity_check, identity_rows

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rows');p.add_argument('--out')
    a=p.parse_args(argv)
    try:result=identity_check(identity_rows(a.rows))
    except (ValueError,KeyError,FileNotFoundError) as exc:p.exit(2,str(exc)+'\n')
    text=json.dumps(result,indent=2)+'\n'
    if a.out:Path(a.out).write_text(text)
    print(text,end='')
    return 0 if result['passes'] else 1

if __name__=='__main__':raise SystemExit(main())
