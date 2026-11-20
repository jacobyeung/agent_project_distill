"""Score a completed annotation join; no guessed defaults for missing stages.

Input JSONL: item_id, room, score (0..100), objects (evidence dictionaries).
Each object must contain target_instance_id and its source-frame-bound evidence.
This script is an analysis endpoint, not the missing live inference adapter.
"""
import argparse
import json
from pathlib import Path
from funnel import STAGES, stage, worse, summarize


def main():
    p=argparse.ArgumentParser()
    p.add_argument('input');p.add_argument('output')
    args=p.parse_args()
    rows=[];objects=[];ids=set()
    for line in Path(args.input).read_text().splitlines():
        r=json.loads(line)
        if r['item_id'] in ids:raise ValueError('duplicate item')
        ids.add(r['item_id'])
        labels=[]
        for e in r['objects']:
            if not e.get('target_instance_id'):
                label,missing='U','target_instance_id'
            else:
                label,missing=stage(e)
            labels.append(label)
            objects.append(dict(item_id=r['item_id'],stage=label,missing=missing))
        rows.append(dict(room=r['room'],group=worse(labels),score=r['score']))
    result=summarize(rows)
    result['object_counts']={s:sum(o['stage']==s for o in objects) for s in STAGES+('U',)}
    result['objects']=objects
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
