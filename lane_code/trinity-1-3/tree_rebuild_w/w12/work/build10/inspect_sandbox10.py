from pathlib import Path
import json
B=Path(__file__).resolve().parent
for name in ('gf1','c8r'):
    report=json.loads((L/'work/build12/proofs/eat1'/name/'run/EAT1_REPORT.json').read_text())
    print(name)
    def walk(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if isinstance(v,str) and ('FileNotFoundError' in v or 'No such file' in v):print(k,v[-1600:])
                elif isinstance(v,(dict,list)):walk(v)
        elif isinstance(obj,list):
            for v in obj:walk(v)
    walk(report['clauses']['A5'])
