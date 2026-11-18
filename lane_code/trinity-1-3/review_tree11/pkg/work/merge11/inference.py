from pathlib import Path
import json,ast,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';T=L/'work/tree_r1'
source=L/'work/build10/inference_inventory.py';s=source.read_text()
O=B/'proofs/inference';O.mkdir(parents=True,exist_ok=True)
old=L/'work/n1fix2/inherited/proofs/audit/INFERENCE_COMPONENTS.json'
(O/'INFERENCE_COMPONENTS.json').write_bytes(old.read_bytes())
s=s.replace("P=L/'work/build10/proofs/audit'","P=L/'work/merge11/proofs/inference'")
s=s.replace("P=L/'work/merge11/proofs/audit'","P=L/'work/merge11/proofs/inference'")
exec(compile(s,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
