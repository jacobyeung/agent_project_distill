from pathlib import Path
import sys,json,base64
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/"work/build24"));import joblib as J
k=L/"work/build24/kits/q";cfg=J.load(k/"k/n.json");spec=J.load(k/"k/p.json")
print("CONFIG",json.dumps({x:cfg[x] for x in ("streams","dev_scene_exclusions","benchmark_scene_exclusions","scene_division","s1_routing","exclusions") if x in cfg},indent=2))
print("R1",json.dumps({x:v for x,v in cfg["r1_training"].items() if any(t in x for t in ("room","k1","registry"))},indent=2))
up={x["sha256"]:x["local_path"] for x in J.load(L/"work/build24m1/UPLOADS_q.json")["files"] if x["opaque_name"].startswith("u/")}
print("UPLOADS",len(up),"spec",len(spec["uploads"]))
for name,pin in list(cfg["streams"].items())+[("pool_selection",cfg["s1_routing"]["selection"])]:
 p=up.get(pin["sha256"]);print("INPUT",name,pin,"staged",bool(p))
 if p:
  v=J.load(p);print("CONTENT",json.dumps({key:v[key] for key in v if key in ("schema","database","count","sources","manifest","room_sets","remove_files","tokenizer","source_scene_exclusions","inputs","division")},indent=2)[:18000])
s=base64.b64decode(json.loads((k/"k/j.json").read_text())["payload"]).decode();(L/"work/build24m2/j_q_before.sh").write_text(s)
k=L/"out/kit_n_go";s=base64.b64decode(json.loads((k/"k/j.json").read_text())["payload"]).decode();(L/"work/build24m2/j_n_before.sh").write_text(s)
