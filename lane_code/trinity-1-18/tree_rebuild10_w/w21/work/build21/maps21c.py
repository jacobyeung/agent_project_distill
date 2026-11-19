from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path.insert(0,str(B));import joblib as J
value=J.load(B/'kits/q/k/l.json')
print(json.dumps(value['staged_inputs'],indent=2))
