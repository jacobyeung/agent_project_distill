import sys,importlib.util,io,contextlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from unittest.mock import patch
F=D/'arming_final';N=D/'native_arm';W0=F/'workspace'
sp=importlib.util.spec_from_file_location('arm_cli_native',L/'out/arm_routing.py');arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
v=J.load(N/'selection.json');r=J.load(N/'receipt.json');out=W0/'out/native_cli'
args=[str(L/'out/arm_routing.py'),str(N/'selection.json'),str(N/'metadata.json'),'--output',str(out),'--routing-base',str(F/'base.json'),'--regenerated-receipt',str(N/'receipt.json'),'--reviewed-selection-sha256',J.sha(N/'selection.json'),'--reviewed-regenerated-sha256',r['database']['sha256'],'--review-verdict',str(N/'RESULT.txt')]
with patch.object(arm,'L',W0),patch.object(sys,'argv',args):
 text=io.StringIO()
 with contextlib.redirect_stdout(text):arm.main()
printed=json.loads(text.getvalue());record=J.load(out/'UPLOADS_ROUTING_ARMED.json')
assert printed['kits']==record['kits'];assert record['native_regeneration']['database_sha256']==r['database']['sha256']
J.write(D/'NATIVE_CLI.json',dict(status='PASS',printed=printed,native_regeneration=record['native_regeneration'],scope='Real CLI parser, helper apply and three decoded scans on synthetic reviewed native receipt; workspace root redirected to fixture copies'))
print('NATIVE CLI PASS')
