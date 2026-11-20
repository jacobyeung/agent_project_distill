from common import *
v=J.load(kit("qd")/"k/l.json");s=J.load(kit("qd")/"k/p.json")
for k in ("closure","record","venv","np","fla","bwrap","model","init"):
 print(k,v.get(k))
print("record sources",[(k,s.get("p_sources",{}).get(k)) for k,h in s["p_files"].items() if h==v["record"]["sha256"]])
