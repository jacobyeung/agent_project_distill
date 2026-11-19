"""Normalize delivered CP2 rows without reading GT arrays or reusing old traces.

The default reads at most 100 input rows. Full-file IO requires an explicit
--full flag and the operator's cluster approval; this module grants none.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from .ground_v312 import TYPES, RowRefusal, parse_roles
from .ground_v312_io import reference, sha

ALIASES = {'absolute_distance_object':'object_abs_distance',
           'relative_distance_object':'object_rel_distance'}


def normalize(row, scenes, T, direct=None):
    typ = ALIASES.get(row['question_type'], row['question_type'])
    if typ not in TYPES:
        raise RowRefusal('direct_type')
    provenance = row['provenance']
    scene = provenance['alias'].split('/')[-1]
    entry = scenes[scene]
    if provenance['gt_sha256'] != entry['gt']['sha256']:
        raise ValueError('source GT pin mismatch')
    if provenance['frame_indices'] != entry['frame_indices']:
        raise ValueError('source frame mismatch')
    if provenance['canonical'] != entry['canonical']:
        raise ValueError('source canonical scene mismatch')
    item = dict(qid=row['qid'],type=typ,source_question_type=row['question_type'],
                scene=scene,question=row['question'],options=row['options'],
                frame_indices=entry['frame_indices'],gt_answer=row['gt_answer'],
                gt_authority='delivered CP2 independent gt_answer',
                source_provenance=provenance)
    item['roles'] = parse_roles(item,T)
    if direct is not None:
        # Exact join validation controls miss eligibility; invalid joins leave normal rows.
        item['direct_canonical'] = direct
    return item


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--input',action='append',required=True)
    parser.add_argument('--scenes',required=True)
    parser.add_argument('--direct-joins')
    parser.add_argument('--rkit-root',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--max-input-rows',type=int,default=100)
    parser.add_argument('--full',action='store_true')
    args=parser.parse_args()
    if args.max_input_rows<=0:raise ValueError('positive input limit required')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=False)
    scenes=json.loads(Path(args.scenes).read_text())
    direct={}
    if args.direct_joins:
        with open(args.direct_joins) as f:
            for line in f:
                row=json.loads(line)
                if row['qid'] in direct:raise ValueError('duplicate direct join')
                direct[row['qid']]=row
    T=reference(args.rkit_root)[0].T
    counts=Counter();seen=set();read=0
    with (out/'ground_items.jsonl').open('x') as output,(out/'dispositions.jsonl').open('x') as rejected:
        for path in args.input:
            if not args.full and read>=args.max_input_rows:break
            with open(path) as source:
                for line in source:
                    if not args.full and read>=args.max_input_rows:break
                    read+=1;row=json.loads(line)
                    if row['qid'] in seen:raise ValueError('duplicate source qid')
                    seen.add(row['qid'])
                    try:item=normalize(row,scenes,T,direct.get(row['qid']))
                    except RowRefusal as exc:
                        counts[str(exc)]+=1
                        rejected.write(json.dumps(dict(qid=row['qid'],reason=str(exc)))+'\n')
                        continue
                    output.write(json.dumps(item,allow_nan=False)+'\n');counts[item['type']]+=1
    receipt=dict(read_rows=read,counts=dict(counts),full=args.full,
                 source_paths=args.input,scenes_sha256=sha(args.scenes),
                 output_sha256=sha(out/'ground_items.jsonl'),training_admitted=False)
    (out/'NORMALIZE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
