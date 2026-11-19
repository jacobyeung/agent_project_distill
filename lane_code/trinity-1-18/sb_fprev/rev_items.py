"""Reviewer's dev item-list check: dataset mix and overlap with the 126 STI/ReSTI captures (capture and room)."""
import json, os, collections
from pathlib import Path
ORCH = Path('/scratch/jjyeung/orch_n30'); B = ORCH / 'sb_framepool/work/blobs'; HERE = Path(__file__).resolve().parent
pre = json.load(open(HERE / 'rev_tokens.json'))['preimages']
caps = [l.split('\t') for l in open(ORCH / 'sb_framepool/out/CAPTURES.tsv').read().splitlines()[1:]]
sti_can = {c[3] for c in caps if 'STI-Bench/ReSTI' in c[5]}; sti_room = {c[4] for c in caps if 'STI-Bench/ReSTI' in c[5]}
DS = {'scannet': 'scannet', 'arkitscenes': 'arkitscenes', 'scannetpp': 'scannetpp', 'scannetppv2': 'scannetpp',
      'd1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes'}
out = {}
for pfx in ['b5853845', '5cd2d5f2', '7a6ac5cc', 'c1c99e4d']:
    f = [x for x in os.listdir(B) if x.startswith(pfx)][0]; items = [json.loads(l) for l in open(B / f)]
    can = set()
    for r in items:
        s = str(r.get('scene')); d = r.get('dataset')
        if s in pre: can.add(pre[s])
        elif '/' in s: can.add(s.replace('scannetppv2/', 'scannetpp/'))
        elif d: can.add(DS.get(d, d) + '/' + s)
        else: can.add(str(r.get('room')).split('/')[0] + '/' + s)
    rooms = {('scannet/' + c.split('/')[1][:9]) if c.startswith('scannet/') else c for c in can}
    out[pfx] = dict(file=f, items=len(items), captures=len(can), datasets=dict(collections.Counter(c.split('/')[0] for c in can)),
                    capture_overlap_126=len(can & sti_can), room_overlap_126=len(rooms & sti_room))
(HERE / 'rev_items.json').write_text(json.dumps(out, indent=1) + '\n'); print(json.dumps(out, indent=1))
