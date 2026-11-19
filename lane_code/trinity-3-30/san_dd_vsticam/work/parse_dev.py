# Parse VSTI dev camera-object (v1/v2/v3) and near/far items at steps 200 and 544 into /tmp/san_dd_vsticam/dev.json
import sys, re, json
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
CAM = ('camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3')
NF = 'obj_obj_relative_pos_nf'
def think(t): return (t or '').split('</think>')[0]
def parse200(r, objs):
    th = think(r['text']); fs = {}; order = None; rel = None
    for m in re.finditer(r'locate the (.+?), first seen in frame (\d+)', th):
        fs[m.group(1)] = int(m.group(2))
    m = re.search(r'the objects are (.+?)\.\s*\n', th + '\n')
    if m: order = [x.strip() for x in m.group(1).split(', then ')]
    m = re.search(r'from the camera viewpoint of frame \d+(?: of \d+)?, the (.+?) is nearer than the (.+?)\.', th)
    if m: rel = (m.group(1), m.group(2))
    return dict(fs=fs, order=order, rel=rel)
def parse544(r, objs):
    th = think(r['text']); dist = {}; cam = None
    m = re.search(r'find the camera \(first seen in frame (\d+)\)', th)
    if m: cam = int(m.group(1))
    m = re.search(r'closest-point distance from the camera to each: (.+?)\.\s*\n', th + '\n')
    if m:
        for part in m.group(1).split('; '):
            mm = re.match(r'(.+?) ([\d.]+) m$', part.strip())
            if mm: dist[mm.group(1)] = float(mm.group(2))
    fs = {mm.group(1): int(mm.group(2)) for mm in re.finditer(r'the ([^()]+?) \(first seen in frame (\d+)\)', th)}
    return dict(dist=dist, cam=cam, fs=fs, think=th)
out = []
for run, step in (('R1', 200), ('S1', 544)):
    for r in K.vsti(run, step, types=list(CAM) + [NF]):
        q = r['question']; k = int(re.search(r'frame (\d+) of 32', q).group(1))
        opts = [o.split('. ', 1)[1] for o in r['options']]
        d = dict(id=r['id'], step=step, type=r['type'], room=r['room'], q=q, opts=opts, gt=r['gt'], pred=r['pred'], score=r['score'],
                 pred_on=r['pred_on'], forced_close=r['forced_close'], k=k, text=think(r['text']))
        if r['type'] == NF:
            m = re.search(r'is (.+?) \[Near/Far\] compared to (.+?)\?', q); d['subj'], d['ref'] = m.group(1), m.group(2)
        d.update(parse200(r, opts) if step == 200 else parse544(r, opts))
        out.append(d)
json.dump(out, open('/tmp/san_dd_vsticam/dev.json', 'w'))
print(len(out))
