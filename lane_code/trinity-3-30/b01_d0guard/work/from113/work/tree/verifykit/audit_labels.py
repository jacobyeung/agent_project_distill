"""Scoring-only B2-compatible object labels from the pinned per-proposal audit."""
import argparse
import csv
import json
from pathlib import Path
from .io import ROOT, SPLIT, cache, rows, write_rows, sha

AUDIT=ROOT/'sam3_audit/out/cache_audit/name_frames.csv'


def label(candidates, out, split='all', oracle_v3_out=None, audit=AUDIT):
    groups=rows(candidates);tuning=set(json.loads(SPLIT.read_text())['tuning_scenes'])
    if split!='all':groups=[g for g in groups if (g['scene'] in tuning)==(split=='tuning')]
    allowed={(g['scene'],g['name']) for g in groups};table={}
    with Path(audit).open() as f:
        for r in csv.DictReader(f):
            if (r['scene'],r['name']) in allowed:
                table[r['scene'],r['name'],int(r['slot'])]=dict(ious=json.loads(r['ious']),visible=r['visible']=='True',scores=json.loads(r['scores']))
    audit_sha=sha(audit);output=[]
    for g in groups:
        def iou(member):
            ref=member['mask_ref'];instances=cache(ref['path'])['frames'][str(ref['slot'])]['phrases'][ref['phrase']]['instances']
            order=sorted(range(len(instances)),key=lambda i:-float(instances[i]['score']))
            j=order.index(ref['instance_index']);a=table[g['scene'],g['name'],member['slot']]
            if abs(a['scores'][j]-instances[ref['instance_index']]['score'])>1e-7:raise ValueError('Audit cache scores differ')
            return a['ious'][j]
        truth={}
        for c in g['candidates']:
            best=max(map(iou,c.get('members') or [c]));representative=iou(c)
            truth[c['candidate_id']]=dict(on_target=best>0,strict_on_target=best>.5,
                representative_on_target=representative>0,max_iou=best,representative_iou=representative)
        visibility=[table[g['scene'],g['name'],k]['visible'] for k in range(32)]
        output.append(dict(object_id=g['object_id'],scene=g['scene'],candidates=truth,absent=not any(visibility),
            frame_presence=visibility,audit_sha256=audit_sha,
            label_definition='E1 any-member IoU > 0; strict IoU > 0.5 and representative overlap reported separately.'))
        if oracle_v3_out and 'v3_slots' not in g:
            g['v3_slots']=sorted(range(32),key=lambda k:(-int(visibility[k]),k))[:4]
            g['v3_presence_source']='GT_PRESENCE_ORACLE'
    write_rows(out,output)
    if oracle_v3_out:write_rows(oracle_v3_out,groups)
    return dict(objects=len(output),scenes=len({g['scene'] for g in groups}),split=split,audit_sha256=audit_sha)


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--candidates',required=True);p.add_argument('--out',required=True)
    p.add_argument('--split',choices=['all','tuning','heldout'],default='all');p.add_argument('--oracle-v3-out');a=p.parse_args()
    print(json.dumps(label(a.candidates,a.out,a.split,a.oracle_v3_out)))

if __name__=='__main__':main()
