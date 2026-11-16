"""k6tk validation (runs on Orchard after k6install.py put the store under ROOT/data2root/k6tk).
usage: k6val.py F ROOT MP4DIR OUT.json
 1. 1% sample of MAP lines: sha256 of the installed file, PNG header size == MAP w/h, decodes with cv2.
 2. every MAP line: size rule (d1/d2 640x480; d3 640x480 for rot none/180, 480x640 for cw/ccw).
 3. ARKit timestamps: |dt| of trajectory-matched frames (all captures, and the AWS val tokens) <= 0.5 ms.
 4. ARKit orientation: stored frames vs the VSI-590K release mp4 (32x32 gray NCC over every mp4 frame) for 10 captures;
    the stored orientation must beat the three other rotations."""
import glob, gzip, hashlib, json, os, random, struct, sys
import numpy as np
import cv2
F, ROOT, MP4, OUTP = sys.argv[1:5]
S = os.path.join(ROOT, "data2root", "k6tk")
plan = json.load(gzip.open(F + "/plan/PLAN.json.gz", "rt"))
cfg = json.load(open(F + "/bin/val_cfg.json"))
rows = [json.loads(l) for l in gzip.open(F + "/k6tk/MAP.jsonl.gz", "rt")]
loc = lambda r: os.path.join(S, r["path"].split("/data2/k6tk/", 1)[1])
out = {}
# 1
random.seed(1)
samp = random.sample(rows, max(1, len(rows) // 100))
bad = {"sha": 0, "hdr": 0, "decode": 0}
for r in samp:
    b = open(loc(r), "rb").read()
    if hashlib.sha256(b).hexdigest() != r["sha256"]: bad["sha"] += 1
    w, h = struct.unpack(">II", b[16:24])
    if (w, h) != (r["w"], r["h"]): bad["hdr"] += 1
    im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
    if im is None or im.shape[1] != w or im.shape[0] != h: bad["decode"] += 1
out["sample_1pct"] = {"n": len(samp), "bad": bad, "by_d": {d: sum(1 for r in samp if r["d"] == d) for d in ("d1", "d2", "d3")}}
# 2
viol = 0
for r in rows:
    if r["d"] == "d3":
        want = (480, 640) if plan["a"][r["s"]]["rot"] in ("cw", "ccw") else (640, 480)
    else:
        want = (640, 480)
    viol += (r["w"], r["h"]) != want
out["size_rule"] = {"lines": len(rows), "violations": viol}
# 3
res = {}
for p in glob.glob(F + "/k6tk/parts/a*/out.jsonl"):
    for l in open(p):
        r = json.loads(l)
        if "frames" in r: res[r["s"]] = r
flag = {t: {n[0]: n[2] for n in e["need"]} for t, e in plan["a"].items()}
def dts(toks, fl):
    v = [abs(fr[4]) for t in toks if t in res for fr in res[t]["frames"] if flag[t].get(fr[0]) == fl]
    return {"n": len(v), "max_ms": max(v) if v else None, "over_0.5ms": sum(x > 0.5 for x in v)}
out["timestamps"] = {"all_trajectory_matched": dts(list(res), 1), "all_no_trajectory_row": dts(list(res), 0),
                     "aws_val_tokens": {t: dts([t], 1) for t in cfg["ts10"]},
                     "ncc_captures": {c["s"]: dts([c["s"]], 1) for c in cfg["ncc"]}}
# 4
def small(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.resize(g, (32, 32), interpolation=cv2.INTER_AREA)
    g -= g.mean()
    return g / (np.linalg.norm(g) + 1e-6)
ROTS = {"same": lambda a: a, "cw": lambda a: cv2.rotate(a, cv2.ROTATE_90_CLOCKWISE),
        "ccw": lambda a: cv2.rotate(a, cv2.ROTATE_90_COUNTERCLOCKWISE), "180": lambda a: cv2.rotate(a, cv2.ROTATE_180)}
byk = {}
for r in rows:
    if r["d"] == "d3": byk.setdefault(r["s"], {})[r["i"]] = r
ncc = {}
for c in cfg["ncc"]:
    t, vid = c["s"], c["vid"]
    mp = [p for p in glob.glob(MP4 + "/**/" + vid + ".mp4", recursive=True)]
    if not mp:
        ncc[t] = {"vid": vid, "error": "mp4 not in release archive"}; continue
    cap = cv2.VideoCapture(mp[0])
    fps, mw, mh = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    V = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        V.append(small(fr).reshape(-1))
    V = np.stack(V)
    ks = sorted(byk.get(t, {}))
    pick = [ks[int(i * (len(ks) - 1) / 5)] for i in range(6)] if len(ks) >= 6 else ks
    fr_res = []
    for k in pick:
        img = cv2.imread(loc(byk[t][k]), cv2.IMREAD_COLOR)
        sc = {}
        for nm, f in ROTS.items():
            a = f(img)
            if (a.shape[1] > a.shape[0]) != (mw > mh):
                sc[nm] = None; continue
            v = V @ small(a).reshape(-1)
            j = int(np.argmax(v)); sc[nm] = [round(float(v[j]), 3), j]
        best = max((x for x in sc if sc[x]), key=lambda x: sc[x][0])
        fr_res.append({"k": k, "best": best, "ncc": sc[best][0], "mp4_frame": sc[best][1], "j_minus_3k": sc[best][1] - 3 * k, "scores": sc})
    ncc[t] = {"vid": vid, "rot": c["rot"], "meta_sky": c["meta_sky"], "mp4_wh": [mw, mh], "mp4_fps": fps, "mp4_frames": len(V),
              "stored_best": sum(f["best"] == "same" for f in fr_res), "frames": len(fr_res),
              "ncc_min": min(f["ncc"] for f in fr_res) if fr_res else None, "j_minus_3k": [f["j_minus_3k"] for f in fr_res], "detail": fr_res}
out["orientation_ncc"] = ncc
out["orientation_summary"] = {"captures": len(ncc), "captures_all_frames_stored_best": sum(1 for v in ncc.values() if v.get("frames") and v["stored_best"] == v["frames"]),
                              "meta_disagree_captures": sum(1 for c in cfg["ncc"] if {"Up": "none", "Left": "cw", "Right": "ccw", "Down": "180"}.get(c["meta_sky"]) != c["rot"])}
json.dump(out, open(OUTP, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "orientation_ncc"}, indent=1))
for t, v in ncc.items():
    print(t, {k: v.get(k) for k in ("vid", "rot", "meta_sky", "mp4_wh", "stored_best", "frames", "ncc_min", "j_minus_3k", "error")})
