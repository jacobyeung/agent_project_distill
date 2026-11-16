import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
v=json.loads((L/'work/kit07ca49df_meta/m/k/b02e4385.json').read_text())
def visit(v, trail=''):
    if isinstance(v,dict):
        for k,x in v.items():
            visit(x,trail+'/'+k)
    elif isinstance(v,list):
        for i,x in enumerate(v):visit(x,trail+'/'+str(i))
    elif isinstance(v,str) and v.startswith('/'):
        print(trail,v)
visit(v)
