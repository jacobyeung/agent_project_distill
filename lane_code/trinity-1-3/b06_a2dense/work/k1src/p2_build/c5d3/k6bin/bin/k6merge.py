"""Merge k6tk part outputs into MAP.jsonl.gz, SCENES.json, RECEIPT.json, INDEX.json, MEMBERS.tsv.gz (tokens only).
usage: k6merge.py F OUTDIR   (F = /project/community/jjyeung/cp4tk_fr; reads F/plan/PLAN.json.gz and F/k6tk/parts/*/)"""
import collections, glob, gzip, hashlib, json, os, sys, tarfile, time
F, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
plan = json.load(gzip.open(F + "/plan/PLAN.json.gz", "rt"))
code = {t: "d3" for t in plan["a"]}
code.update({t: e["g"] for t, e in plan["v"].items()})
need = {t: sorted({n[0] for n in e["need"]}) for t, e in plan["a"].items()}
need.update({t: sorted(set(e["need"])) for t, e in plan["v"].items()})
flag = {t: {n[0]: n[2] for n in e["need"]} for t, e in plan["a"].items()}
parts = sorted(p for p in glob.glob(F + "/k6tk/parts/*") if os.path.isfile(p + "/DONE"))
res, shards, member_of = {}, [], {}
for p in parts:
    for line in open(p + "/out.jsonl"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if "error" in r and r["s"] in res and "error" not in res[r["s"]]:
            continue
        res[r["s"]] = r
    lst = json.load(open(p + "/LIST.json"))
    for s in lst["shards"]:
        tp = os.path.join(p, s["name"])
        n = 0
        with tarfile.open(tp, "r:") as tf:
            for ti in tf:
                sha = os.path.basename(ti.name)[:-4]
                member_of.setdefault(sha, s["name"]); n += 1
        assert n == s["n"], (tp, n, s["n"])
        shards.append({"name": s["name"], "part": os.path.basename(p), "n": s["n"], "bytes": s["bytes"], "sha256": s["sha256"]})
lines, scenes, used = [], {}, {}
cnt = {}
dts = collections.defaultdict(list)
past_end = collections.Counter()
for t in sorted(need):
    d = code[t]
    r = res.get(t)
    status = "pending" if r is None else ("error" if "error" in r else "ok")
    got = {}
    if status == "ok":
        for fr in r["frames"]:
            got[fr[0]] = (fr[1], fr[2], fr[3])
            if d == "d3":
                dts[flag[t].get(fr[0], 0)].append(abs(fr[4]))
    for k in sorted(got):
        sha, w, h = got[k]
        if sha not in member_of:
            raise SystemExit(f"sha missing from shards: {t} {k}")
        lines.append(json.dumps({"d": d, "s": t, "i": k, "path": f"/data2/k6tk/{sha[:2]}/{sha}.png", "sha256": sha, "w": w, "h": h}))
        used[sha] = member_of[sha]
    miss = sorted(set(need[t]) - set(got))
    tot = plan["total"][t]
    ent = {"total_num_frames": tot}
    if miss:
        ent["misses"] = miss
    if status != "ok":
        ent["status"] = status
    scenes.setdefault(d, {})[t] = ent
    c = cnt.setdefault(d, {"scenes": 0, "scenes_ok": 0, "needed": 0, "mapped": 0, "misses": 0, "misses_past_total": 0,
                           "mapped_index_ge_total": 0})
    c["scenes"] += 1; c["scenes_ok"] += status == "ok"; c["needed"] += len(need[t]); c["mapped"] += len(got); c["misses"] += len(miss)
    c["misses_past_total"] += sum(1 for k in miss if k >= tot)
    c["mapped_index_ge_total"] += sum(1 for k in got if k >= tot)
def wr(name, data, mode="w"):
    tmp = os.path.join(OUT, "." + name + ".tmp")
    if name.endswith(".gz"):
        with gzip.open(tmp, "wt") as f:
            f.write(data)
    else:
        with open(tmp, "w") as f:
            f.write(data)
    os.replace(tmp, os.path.join(OUT, name))
wr("MAP.jsonl.gz", "\n".join(lines) + "\n")
wr("SCENES.json", json.dumps(scenes))
wr("MEMBERS.tsv.gz", "".join(f"{s}\t{used[s]}\n" for s in sorted(used)))
idx = {"store": "/data2/k6tk", "member_layout": "<sha[:2]>/<sha>.png; extract every shard into <root>/data2root/k6tk/",
       "shards": shards, "members_total": sum(s["n"] for s in shards), "unique_members": len(member_of), "map_unique_shas": len(used)}
wr("INDEX.json", json.dumps(idx, indent=1))
def q(v, p):
    v = sorted(v)
    return round(v[min(len(v) - 1, int(p * len(v)))], 3) if v else None
bsha = {}
for n in ["wa.py", "wd.py", "k6run.py", "k6pack.py", "k6merge.py", "k6job.sh"]:
    bsha[n] = hashlib.sha256(open(os.path.join(F, "bin", n), "rb").read()).hexdigest()
bsha["PLAN.json.gz"] = hashlib.sha256(open(F + "/plan/PLAN.json.gz", "rb").read()).hexdigest()
for a in ["scannet.tar.gz", "scannetppv2.tar.gz"]:
    okf = F + "/media/" + a + ".ok"
    bsha["media/" + a] = open(okf).read().strip() if os.path.exists(okf) else None
rec = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "store": "/data2/k6tk", "map_lines": len(lines), "counts": cnt,
       "map_unique_pngs": len(used), "png_bytes_in_shards": None, "shards": len(shards), "shard_bytes": sum(s["bytes"] for s in shards),
       "max_members_per_shard": max(s["n"] for s in shards) if shards else 0, "parts": [os.path.basename(p) for p in parts],
       "arkit_match_abs_dt_ms": {("trajectory_row" if k else "no_trajectory_row"): {"n": len(v), "p50": q(v, .5), "p99": q(v, .99), "max": q(v, 1.0)}
                                 for k, v in dts.items()},
       "builder_sha256": bsha,
       "rules": {"d3": "Apple raw lowres_wide range fetch; k = round((t - t0) * 10) on lowres_wide.traj; member matched within 2 ms (trajectory row) or 10.5 ms (t0 + k/10); "
                       "rotation from pose gravity (Up none, Left 90 cw, Right 90 ccw, Down 180), then 2.5x cubic resize (480x640 or 640x480); PNG via cv2 level 3",
                 "d1_d2": "VSI-590K release mp4 (HF nyu-visionx/VSI-590K rev 346fbd4e), mp4 frame == raw index, 640x480 (INTER_AREA only if different), PNG via cv2 level 3",
                 "misses": "indices with no source frame (past the stream end) are misses, never clamped"}}
wr("RECEIPT.json", json.dumps(rec, indent=1))
print(json.dumps({k: rec[k] for k in ("map_lines", "counts", "map_unique_pngs", "shards", "shard_bytes", "arkit_match_abs_dt_ms")}))
