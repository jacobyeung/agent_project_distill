from pathlib import Path
import sys,json,base64,hashlib,os
L=Path(__file__).resolve().parents[2];D=L/"work/build24m4f"
sys.path[:0]=[str(L/"work/build24m4d"),str(L/"work/tree_r1")]
import joblib as J
def kit(name):return L/("out/kit_n_go" if name=="n_go" else "out/kit_qd" if name=="qd" else "work/build24/kits/"+name)
