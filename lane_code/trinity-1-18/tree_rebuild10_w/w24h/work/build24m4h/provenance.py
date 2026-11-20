exec((__import__("pathlib").Path(__file__).parent/"inspect.py").read_text().split("print(\"tree\"")[0])
paths=[W/"ext/pwrap/k/7.json",W/"ext/pwrap/k/archive.json",W/"ext/pwrap/k/binding_evidence.json",W/"ext/pwrap/k/launch.json",W/"ext/pwrap/runs_partial/binding.json",W/"ext/pwrap/runs_partial/attempt_172660.json",W/"work/conf23d/pkg/work/build21/upload/u/0bc9414250b2ce082a5a1a74fb9421da991f0b794b6ed6c362ab96e92c11dea6"]
for p in paths:
 v=J.load(p);print("FILE",p,"HASH",J.sha(p),"KEYS",list(v))
 for k,x in v.items():
  if k in ("files","source_files","sources","implementation"):print(k,"entries",len(x),"pool",x.get("student_pilot/s1_pool.py") if isinstance(x,dict) else "")
  elif len(str(x))<1200:print(k,x)
