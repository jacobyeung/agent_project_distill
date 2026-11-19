exec((__import__("pathlib").Path(__file__).parent/"audit.py").read_text().split("for name in (")[0])
k=L/"work/build24/kits/q";spec=J.load(k/"k/p.json");ups={v["sha256"]:v for v in J.load(L/"work/build24d/UPLOADS_q.json")["files"] if v["opaque_name"].startswith("u/")};st={v["sha256"] for v in spec["uploads"]}
rows=J.load(D/"PATHS_BEFORE.json")
for h,r in {r["sha256"]:r for r in rows if r["kind"]=="pin" and r["path"].startswith("/scratch/jjyeung")}.items():
 print(h[:12],"stage",h in st,"upload",h in ups,"bytes",Path(r["path"]).stat().st_size,r["where"])
print("uploads",len(ups),len(st));print("upload sample",spec["uploads"][:1]);print("keys",spec.keys())
print("data absolute configs",[(r["where"],r["path"]) for r in rows if r["kind"]=="absolute" and r["where"].startswith("q/k/n.json") and not ("sha" in r["where"] or r["path"].startswith(("/scratch/jjyeung","/tmp")))])
