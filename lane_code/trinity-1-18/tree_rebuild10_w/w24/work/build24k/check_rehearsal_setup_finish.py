# Complete metadata after the extraction-only import failure; never run native stages twice.
from pathlib import Path
import sys,os,json,base64,hashlib,shutil,tarfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths2 import L,D,R,reseal
sys.path.insert(0,str(L/'work/build24'))
import joblib as J
selected=Path(sys.argv[1]).resolve();selected_seal=J.seal(selected)
kit=R/'kit_n_go';control=J.load(kit/'k/a.json');source=L/'work/build24f/rehearsal3'
assert R.name=='rehearsal_k2_probe' and not (R/'SETUP.json').exists() and not (R/'RUN_STARTED.json').exists()
assert J.seal(kit)==selected_seal
script=D/'make_rehearsal_k2.py'
text=script.read_text();tail=text[text.index("sys.path.insert(0,str(R/'source'))"):]
exec(compile(tail,str(script),'exec'))
