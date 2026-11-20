import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for name,cfg in (("P",J.load(input_file("b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad"))),("N",J.load(kit("n")/"k/c.json"))):
 J.write(D/(name+"_CONFIG.json"),cfg)
 print(name,"sampling",cfg.get("r2_sampling"),"mix",cfg.get("r1_training",{}).get("mix"))
 for key,pin in cfg.get("r2_sampling",{}).items():
  if isinstance(pin,dict) and "sha256" in pin:
   p=input_file(pin["sha256"]);v=J.load(p);J.write(D/(name+"_"+key+".json"),v)
   print(name,key,p,"KEYS",list(v))
   if key!="indices":print(json.dumps(v,indent=2)[:20000])
