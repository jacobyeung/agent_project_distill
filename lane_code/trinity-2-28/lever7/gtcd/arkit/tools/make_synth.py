"""Make a rehearsal directory: synthetic lowres_wide.zip files (60 fps deflated PNG members named like Apple's), a plan in
PLAN_ARKIT.json form (10 fps traj rows, stride 2 plus 32 anchors, timestamps offset <= 0.5 ms from members), and a
FRAMES_GTC-form index whose anchor sha256 values come from an independent read (python zipfile + warule.encode).
Capture s2 gets one wrong anchor sha256 (it must be rejected).
usage: make_synth.py TEST_DIR PORT"""
import hashlib, json, os, sys, zipfile
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
import warule
sys.path.insert(0, '/scratch/jjyeung/orch_n30/lever7/gtcd/kit')
import gtc_common as GC

T, PORT = sys.argv[1], int(sys.argv[2])
os.makedirs(os.path.join(T, 'plan'), exist_ok=True); os.makedirs(os.path.join(T, 'served'), exist_ok=True)
rng = np.random.default_rng(7)
plan, gtc = {}, []
for cid, rows, t0, rot in (('90000001', 140, 500.0123, 'none'), ('90000002', 100, 7700.4567, '180')):
    zp = os.path.join(T, 'www/raw/Training', cid, 'lowres_wide.zip'); os.makedirs(os.path.dirname(zp), exist_ok=True)
    mts = [round(t0 + j / 60.0, 3) for j in range(rows * 6 + 3)]
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('lowres_wide/', b'')
        order = list(range(len(mts))); rng.shuffle(order)          # Apple's zips are not in time order
        for j in order:
            img = np.zeros((192, 256, 3), np.uint8)
            img[:] = (j % 255, (3 * j) % 255, 80)
            cv2.circle(img, (int(40 + j % 170), 96), 20, (255, 255 - j % 200, 30), -1)
            img[::17, :, 2] = 200
            img = (img.astype(int) + rng.integers(0, 3, img.shape)).clip(0, 255).astype(np.uint8)
            z.writestr('lowres_wide/%s_%.3f.png' % (cid, mts[j]), cv2.imencode('.png', img)[1].tobytes())
    traj = [mts[6 * k] + float(rng.uniform(-0.0005, 0.0005)) for k in range(rows)]
    anchors = sorted(set(int(round(x)) for x in np.linspace(1, rows - 3, 32)))
    assert len(anchors) == 32
    idx = GC.dense_indices(anchors, 2)
    plan[cid] = dict(u='http://127.0.0.1:%d/raw/Training/%s/lowres_wide.zip' % (PORT, cid), rot=rot,
                     need=[[k, traj[k], 1] for k in idx], anchors=anchors)
    frames = []
    with zipfile.ZipFile(zp) as z:
        for s, k in enumerate(anchors, 1):
            png, _, _ = warule.encode(z.read('lowres_wide/%s_%.3f.png' % (cid, mts[6 * k])), rot)
            p = os.path.join(T, 'served', '%s_%06d.png' % (cid, k)); open(p, 'wb').write(png)
            h = hashlib.sha256(png).hexdigest()
            if cid == '90000002' and s == 5:
                h = '0' * 64
            frames.append(dict(slot=s, index=k, path=p, sha256=h, bytes=len(png)))
    gtc.append(dict(capture='arkitscenes/' + cid, native='d3/' + cid, frames=frames, anchor_indices=anchors))
json.dump(dict(captures=plan), open(os.path.join(T, 'plan/PLAN_ARKIT.json'), 'w'))
json.dump(dict(captures=gtc), open(os.path.join(T, 'FRAMES_GTC_SYNTH.json'), 'w'))
print('made', T, {c: len(e['need']) for c, e in plan.items()})
