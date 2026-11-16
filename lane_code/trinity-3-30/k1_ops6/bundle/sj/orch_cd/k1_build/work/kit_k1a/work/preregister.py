import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate,k1_report
out=Path(__file__).resolve().parents[1]/'out';p=out/'K1_RULES.json'
if p.exists():
 assert json.loads(p.read_text())==k1_report.RULES
else:p.write_text(json.dumps(k1_report.RULES,indent=2)+'\n')
(out/'K1_RULES.sha256').write_text(gate.sha(p)+'  K1_RULES.json\n')
print(gate.sha(p))
