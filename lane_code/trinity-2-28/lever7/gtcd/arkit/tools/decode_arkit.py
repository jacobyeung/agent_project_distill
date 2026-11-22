"""Decode the fetched ARKit members by k6 wa.py's rule into the layout gtcd/kit/dense.py --frames-dir expects
(<frames>/<id>/<traj row:06d>.png), and check every anchor's sha256 against FRAMES_GTC.json.
Per capture: the picks are recomputed from the plan and the fetched central directory (wa.py's nearest member, 2 ms) and must
equal the fetcher's _picks.json; each member's local header must name the picked member. A capture whose anchors all match,
with no miss, goes to <frames>/<id>/. A capture with any anchor mismatch, miss or missing member goes to
<rejected>/<id>/ and is reported, not substituted (dense.py then finds no source for it). Existing output is never overwritten.
usage: decode_arkit.py --raw DIR --plan PLAN_ARKIT.json --frames DIR --rejected DIR --manifest OUT.json
                       [--frames-gtc FRAMES_GTC.json] [--captures a,b] [--workers 8]"""
import argparse, hashlib, json, os, struct, sys, time
from multiprocessing import Pool
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import zipcd

FRAMES_GTC = '/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'
TOL_TRAJ, TOL_INTERP = 0.002, 0.0105


def sha(b):
    return hashlib.sha256(b).hexdigest()


def one(job):
    import cv2, warule
    cid, e, anchors, raw, frames, rejected = job
    t0 = time.monotonic()
    ent = dict(id=cid, capture='arkitscenes/' + cid, rot=e['rot'], cv2=cv2.__version__, dense=len(e['need']), anchors=len(anchors),
               written=0, anchor_sha_equal=0, mismatches=[], misses=[], missing_members=[], errors=[])
    d = os.path.join(raw, cid)
    dst_ok, dst_bad = os.path.abspath(os.path.join(frames, cid)), os.path.abspath(os.path.join(rejected, cid))
    if os.path.exists(dst_ok) or os.path.exists(dst_bad):
        ent.update(status='EXISTS', note='output exists; not overwritten'); return ent
    try:
        pk = json.load(open(os.path.join(d, '_picks.json')))
        fr = zipcd.frames_of(zipcd.parse_cd(open(os.path.join(d, '_cd.bin'), 'rb').read()))
    except OSError as x:
        ent.update(status='SOURCE_MISSING', errors=[repr(x)[:200]]); return ent
    ts = np.array([f[0] for f in fr]); picks = []
    for k, t, flag in e['need']:
        b = zipcd.nearest(ts, t)
        if b is None or abs(ts[b] - t) > (TOL_TRAJ if flag else TOL_INTERP):
            ent['misses'].append(k); continue
        picks.append([k, b, fr[b][1]])
    if [p[:3] for p in pk['picks']] != picks:
        ent['errors'].append('recomputed picks differ from the fetcher _picks.json')
    tmp = os.path.join(frames, '.tmp_' + cid); os.makedirs(tmp)
    for k, b, name in picks:
        f = fr[b]; p = os.path.join(d, 'm', os.path.basename(name) + '.bin')
        try:
            buf = open(p, 'rb').read()
        except OSError:
            ent['missing_members'].append(k); continue
        try:
            n2 = struct.unpack('<H', buf[26:28])[0]
            if buf[30:30 + n2].decode('utf-8', 'replace') != name:
                raise RuntimeError('local header names %r' % buf[30:30 + n2][:80])
            png, _, hw = warule.encode(warule.member_payload(buf, f[2], f[3]), e['rot'])
        except Exception as x:
            ent['errors'].append('%d: %s' % (k, repr(x)[:200])); continue
        if hw != (480, 640):
            ent['errors'].append('%d: output %s' % (k, hw))
        with open(os.path.join(tmp, '%06d.png' % k), 'wb') as g:
            g.write(png)
        ent['written'] += 1
        a = anchors.get(k)
        if a is not None:
            s = sha(png)
            if s == a['sha256']:
                ent['anchor_sha_equal'] += 1
            else:
                mine = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR); served = cv2.imread(a['path'], cv2.IMREAD_COLOR)
                mx = int(np.abs(mine.astype(int) - served.astype(int)).max()) if served is not None and served.shape == mine.shape else None
                ent['mismatches'].append(dict(index=k, slot=a['slot'], sha256=s, served_sha256=a['sha256'], max_abs=mx))
    anchor_missing = [k for k in anchors if k in ent['misses'] or k in ent['missing_members']]
    if ent['mismatches'] or ent['anchor_sha_equal'] != len(anchors):
        ent['status'] = 'SHA_MISMATCH' if ent['mismatches'] else 'SOURCE_MISSING'
    elif ent['errors'] or ent['misses'] or ent['missing_members']:
        ent['status'] = 'FRAMES_MISSING'
    else:
        ent['status'] = 'OK'
    ent['anchor_missing'] = anchor_missing
    if ent['status'] == 'OK':
        os.rename(tmp, dst_ok); ent['dir'] = dst_ok
    else:
        os.makedirs(rejected, exist_ok=True); os.rename(tmp, dst_bad); ent['dir'] = dst_bad
    ent['seconds'] = round(time.monotonic() - t0, 1)
    with open(os.path.join(ent['dir'], 'DECODE.json'), 'w') as g:
        json.dump(ent, g, indent=1)
    return ent


def main():
    ap = argparse.ArgumentParser()
    for a in ('--raw', '--plan', '--frames', '--rejected', '--manifest'):
        ap.add_argument(a, required=True)
    ap.add_argument('--frames-gtc', default=FRAMES_GTC)
    ap.add_argument('--captures', default='')
    ap.add_argument('--workers', type=int, default=8)
    x = ap.parse_args()
    plan = json.load(open(x.plan))['captures']
    G = {c['capture'].split('/', 1)[1]: c for c in json.load(open(x.frames_gtc))['captures'] if c['capture'].startswith('arkitscenes/')}
    only = [c for c in x.captures.split(',') if c]
    ids = sorted(only or plan)
    if set(ids) - set(plan) or set(ids) - set(G):
        raise SystemExit('unknown captures: %s' % sorted((set(ids) - set(plan)) | (set(ids) - set(G))))
    os.makedirs(x.frames, exist_ok=True)
    jobs = [(c, plan[c], {f['index']: f for f in G[c]['frames']}, x.raw, x.frames, x.rejected) for c in ids]
    jobs.sort(key=lambda j: -len(j[1]['need']))
    with Pool(min(x.workers, 8, len(jobs))) as p:
        ents = p.map(one, jobs, chunksize=1)
    ents.sort(key=lambda e: e['id'])
    st = {}
    for e in ents:
        st[e['status']] = st.get(e['status'], 0) + 1
    man = dict(time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), host=os.uname().nodename, rule='k6 wa.py: inflate, cv2.imdecode COLOR, '
               'rotate by plan rot, 2.5x INTER_CUBIC, PNG compression 3', frames_dir_template=os.path.join(os.path.abspath(x.frames), '{id}'),
               status=st, frames=sum(e['written'] for e in ents if e['status'] == 'OK'),
               anchors_equal=sum(e['anchor_sha_equal'] for e in ents), anchors=sum(e['anchors'] for e in ents), captures=ents)
    with open(x.manifest + '.tmp', 'w') as g:
        json.dump(man, g, indent=1)
    os.replace(x.manifest + '.tmp', x.manifest)
    for e in ents:
        print(e['id'], e['status'], 'frames', e['written'], 'anchors', '%d/%d' % (e['anchor_sha_equal'], e['anchors']),
              'misses', len(e['misses']), 'errors', len(e['errors']))
    print('STATUS', json.dumps(st), 'anchors_equal', man['anchors_equal'], 'of', man['anchors'])
    return 0 if set(st) == {'OK'} else 1


if __name__ == '__main__':
    sys.exit(main())
