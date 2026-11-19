"""Bind the environment's editable SAM3 import to the staged source tree."""
import ast
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/'payload/environment/lib/python3.12/site-packages/__editable___sam3_0_1_0_finder.py'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    before=sha(P); source=P.read_text(); lines=source.splitlines()
    old='/home/jjyeung/agent_project/agent/third_party/sam3/sam3'
    new=[]
    for line in lines:
        if line.startswith('MAPPING:'):
            new.append("_SAM3 = Path(__file__).resolve().parents[4] / 'files/scratch/jjyeung/b01ec87a6f29b/d/s/sam3'")
            new.append("MAPPING: dict[str, str] = {'sam3': str(_SAM3)}")
        elif line.startswith('NAMESPACES:'):
            names=ast.literal_eval(line.split(' = ',1)[1])
            pairs=[repr(k)+': [str(_SAM3 / '+repr(v[0].removeprefix(old+'/'))+')]' for k,v in names.items()]
            new.append('NAMESPACES: dict[str, list[str]] = {'+', '.join(pairs)+'}')
        else: new.append(line)
    P.write_text('\n'.join(new)+'\n')
    record=dict(path=str(P),before_sha256=before,after_sha256=sha(P),command='python -B relocate_environment.py',
                input_sha256={str(P):before,str(Path(__file__)):sha(Path(__file__))})
    (ROOT/'out/ENV_RELOCATION.json').write_text(json.dumps(record,indent=1)+'\n')

if __name__=='__main__': main()
