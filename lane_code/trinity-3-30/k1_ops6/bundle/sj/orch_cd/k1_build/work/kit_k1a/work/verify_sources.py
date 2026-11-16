import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
def verify():
 p=Path(__file__).resolve().parents[1]/'out/DEPENDENCIES.json';pins=json.loads(p.read_text())
 for path,expected in pins.items():
  if gate.sha(path)!=expected:raise ValueError('Read-only dependency changed: '+path)
 return len(pins)
if __name__=='__main__':print(json.dumps(dict(verified_source_files=verify())))
