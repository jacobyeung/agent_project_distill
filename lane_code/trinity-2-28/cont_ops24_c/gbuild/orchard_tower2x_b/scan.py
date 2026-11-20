"""Scan runnable source now and every placement member after a verified build."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parent
WORDS=('split','revsi','vsibench','scannet','arkit','distill','qgen','sam','qwen','h1','h10','head','routing',
       'faithful','devs1','g3t','camera','displacement','rotation','movement','distance','r0','direction','own',
       'room','selector','parity','benchmark','dataset','model','tower','coverage','orchard')

def scan(text):
    tokens=re.findall(r'[A-Za-z][A-Za-z0-9]*',text)
    return sorted({t for t in tokens if any(w==t.lower() or len(w)>3 and t.lower().startswith(w) for w in WORDS)})

def main():
    built=(ROOT/'BUILD.json').is_file()
    build=json.loads((ROOT/'BUILD.json').read_text()) if built else None
    names=build['bound_files']+['o_place.sh','o_cpu.sh','o_check_sub.sh','o_fetch.sh','SUBMIT.cmd'] if built else ['0.py','2.py']
    checked=[]
    for name in names:
        assert not scan(name),(name,scan(name))
        if name=='8.tgz':
            with tarfile.open(ROOT/name) as t:
                for member in t:
                    assert member.isfile() and re.fullmatch(r'[a-f0-9]{64}\.png',member.name)
                    blob=t.extractfile(member).read()
                    assert hashlib.sha256(blob).hexdigest()+'.png'==member.name
                    from PIL import Image
                    with Image.open(io.BytesIO(blob)) as im:assert im.size==(256,192)
            checked.append(dict(file=name,lowres_only=True));continue
        raw=(ROOT/name).read_text()
        if name=='1.json':
            cfg=json.loads(raw)
            assert all(re.fullmatch('x[0-9a-z]+',k) for k in cfg)
            for row in cfg['x3']:
                assert all(re.fullmatch('x[0-9a-z]+',k) for k in row)
                assert re.fullmatch('[a-f0-9]{16}',row['x0'])
            checked.append(dict(file=name,input_data=True));continue
        if name=='o_place.sh':
            tree=ast.parse(raw.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0])
            node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='assets' for x in n.targets))
            assets=ast.literal_eval(node.value)
            assert set(assets)==set(build['bound_files'])
            for n,b in assets.items():assert base64.b64decode(b)==(ROOT/n).read_bytes()
            raw=raw[:raw.index('assets=')]+raw[raw.index('\ndata=',raw.index('assets=')):]
        assert not scan(raw),(name,scan(raw))
        if name.endswith(('.sh','.cmd')):subprocess.run(['bash','-n',str(ROOT/name)],check=True)
        if name.endswith('.py'):compile(raw,name,'exec')
        checked.append(dict(file=name,passed=True))
    for p in ROOT.glob('*.py'):compile(p.read_text(),str(p),'exec')
    if built:assert build['placement_bytes']+build['return_reserve_bytes']<build['project_budget_bytes']
    value=dict(source_scan_passed=True,complete_placement_scan=built,files=checked,
               status='complete' if built else 'partial: build awaits verified recipe and placement decision',
               exception='Only opaque-key 1.json values may contain inherited API names and data identities.')
    (ROOT/('SCAN.json' if built else 'SCAN_SOURCE.json')).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value))

if __name__=='__main__':main()
