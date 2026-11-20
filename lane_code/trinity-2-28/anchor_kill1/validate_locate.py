"""Independent raster check and explicit sensitivity to worded frame citations."""
import collections
import gzip
import json
from pathlib import Path
import re
import numpy as np
import anchor_analysis as A

ROOT = Path(__file__).resolve().parent
gt = json.loads((ROOT/'raster_visibility.json').read_text())
claims = [json.loads(x) for x in (ROOT/'locate_claims.jsonl').open()]
by_scene = collections.defaultdict(list)
for c in claims:
    if c['status'] in ('resolved_unique','resolved_multiple'):
        by_scene[c['scene']].append(c)
checked = 0
for scene, rows in by_scene.items():
    with np.load(gt[scene]['path'], allow_pickle=False) as z:
        inst, valid = z['inst'], z['valid']
        for c in rows:
            ids = c['gt_instance_ids']
            fractions = [[np.count_nonzero(inst[f] == iid)/inst[f].size if valid[f] else 0.
                          for f in range(32)] for iid in ids]
            visible_any = any(v >= .01 for fs in fractions for v in fs)
            visible = c['valid_citation'] and any(fs[int(c['frame'])-1] >= .01 for fs in fractions)
            assert c['visible_any'] == visible_any
            assert c['visible'] == visible
            checked += 1

# Keep the registered numeric-citation result separate from semantic worded-frame sensitivity.
ordinals = {'first':1,'initial':1,'second':2,'third':3,'fourth':4,'fifth':5,'sixth':6,
            'seventh':7,'eighth':8,'ninth':9,'tenth':10,'last':32}
rx = re.compile(r'^Step \d+: find (?:the )?(.+?), first seen (.+)', re.I)
word = re.compile(r'\b('+'|'.join(ordinals)+r') frame\b', re.I)
extended = list(claims)
extra = []
ambiguous = []
for step in (400,600):
    for line in gzip.open(ROOT/f'direct{step}.jsonl.gz','rt'):
        r=json.loads(line)
        if r['family'] != 'main':
            continue
        for text in r['arms']['B2048']['trace'].splitlines():
            m=rx.search(text)
            if not m or A.NUMERIC_FRAME.search(text) or not re.search(r'\bframe\b',text):
                continue
            noun, desc=m.groups()
            wm=word.search(desc)
            if not wm:
                ambiguous.append(dict(step=step,item_id=r['item_id'],scene=r['scene'],line=text,
                                      reason='no unique anchor index; spatial frame description or explicit time'))
                continue
            for name in re.split(r' and (?:the )?',noun):
                c=dict(step=step,item_id=r['item_id'],scene=r['scene'],room=r['room'],
                       question_type=r['question_type'],dataset=r['scene'].split('/')[0],
                       noun=name.strip().casefold(),frame_text=str(ordinals[wm.group(1).lower()]),
                       line=text,worded_frame=True)
                c=A.score_claim(c,gt.get(r['scene']),r['raw']['arms']['B2048']['source_frame_indices'])
                extra.append(c)
                extended.append(c)
result=dict(independently_checked_numeric_claims=checked, assertion='all raw raster counts agree',
            worded_extra_claims=extra, ambiguous_frame_statements=ambiguous, steps={})
for step in (400,600):
    cs=[c for c in extended if c['step']==step]
    orig=[c for c in claims if c['step']==step]
    unique=[c for c in orig if c['unique'] and c['visible_any'] and c['visible'] is not None]
    valid=[c for c in unique if c['valid_citation']]
    groups=[]
    for fields in [('dataset',),('question_type',),('dataset','question_type')]:
        for key in sorted({tuple(r[k] for k in fields) for r in cs}):
            groups.append(dict(group=dict(zip(fields,key)),**A.summarize_claims(
                [r for r in cs if tuple(r[k] for k in fields)==key])))
    result['steps'][str(step)]=dict(extended=A.summarize_claims(cs),groups=groups,
          numeric_valid_index_only=A.rate(valid,lambda c:c['visible']),
          numeric_invalid_eligible=sum(not c['valid_citation'] for c in unique))
A.write_json('locate_validation.json',result)
print(json.dumps(dict(independent_claims=checked,extra_claims=len(extra),ambiguous=len(ambiguous),
      extended={s:r['extended']['unique_instance_conditional'] for s,r in result['steps'].items()}),indent=2))
