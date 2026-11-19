from pathlib import Path
import shutil,sys
r=Path(sys.argv[1]);s=Path(sys.argv[2])
shutil.copyfile(s/"request.json",r/"r.json")
shutil.copyfile(s/"roomcfg.json",r/"n.json")
