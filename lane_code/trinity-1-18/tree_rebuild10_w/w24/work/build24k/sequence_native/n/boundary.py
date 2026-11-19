from pathlib import Path
import shutil,sys,json
r=Path(sys.argv[1]);s=Path(sys.argv[2])
v=json.loads((r/"r.json").read_text());req=json.loads((s/"request.json").read_text())
v["_resolved"]["config"]=json.loads((s/"own.json").read_text());v["_paths"]=req["_paths"]
(r/"r.json").write_text(json.dumps(v))
shutil.copyfile(s/"roomcfg.json",r/"n.json")
