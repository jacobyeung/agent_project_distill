"""Report materializer identity without changing or admitting rows."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tree'))
from student_pilot.h1 import canonical_row, materialize, MaterializeRefusal


def check(rows):
    counts=Counter();by_type={};refusals=Counter()
    for source in rows:
        row=canonical_row(source);kind=row.get('question_type',row.get('type','unknown'))
        d=by_type.setdefault(kind,Counter()); counts['rows']+=1;d['rows']+=1
        try:
            printed={e['call_id']:e for e in row.get('events',[]) if e['kind']=='tool_response'}
            target=materialize(row,printed)['target']
            key='identical' if target==row['target'] else 'different'
            counts[key]+=1;d[key]+=1
        except MaterializeRefusal as e:
            counts['refused']+=1;d['refused']+=1;refusals[e.reason]+=1
    return dict(**counts,identity_rate=counts['identical']/counts['rows'] if counts['rows'] else None,
                refusal_reasons=dict(refusals),by_type=by_type)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('rows');a=p.parse_args()
    with open(a.rows) as f: print(json.dumps(check(json.loads(s) for s in f if s.strip()),indent=2))
