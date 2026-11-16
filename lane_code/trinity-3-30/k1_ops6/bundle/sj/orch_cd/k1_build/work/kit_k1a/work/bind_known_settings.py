import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
out=Path(__file__).resolve().parents[1]/'out';p=out/'GPU_SETTINGS.template.json';s=json.loads(p.read_text())
artifact=gate.ROOT/'evalx/inbox/20261114T141906Z_cp2_m544_artifact.json';a=json.loads(artifact.read_text())
s['artifact']=dict(path=str(artifact),sha256=gate.sha(artifact));s['config']['sha256']=a['config_sha256']
s['tower_weights']['sha256']='d460957bb1c8a8c228d83ab10bad8a6dbcf80b03f29d7fbebf9c0f2c1c25f702'
s['tower_config']['sha256']='5aeb2acd008d41a1cac52e10216fbf35e8dfeb2ce26b89bb24e7ccc4ee0817d7'
s['sam_receipt']['sha256']=gate.sha(s['sam_receipt']['path'])
p.write_text(json.dumps(s,indent=2)+'\n')
