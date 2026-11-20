from pathlib import Path
import json
L=Path.cwd();m=json.loads((L/"work/build24m4u/PACKAGE_MANIFEST.json").read_text());seen=set()
for n,v in m["files"].items():
 if v.get("type")=="file" and n.endswith((".tar",".tgz",".tar.gz",".zip")) and v["sha256"] not in seen:
  seen.add(v["sha256"])
  if not any(x in n for x in ("t_", "fixture", "proofs", "resolver", "real_", "pc_", "rd_mount", "tree", "publication")):print(v["bytes"],n)
