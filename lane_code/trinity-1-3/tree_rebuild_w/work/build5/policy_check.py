"""Check containment predicates without creating forbidden paths or child jobs."""
import ast
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit,parse_qs,unquote
L=Path(__file__).resolve().parents[2]
out=L/'work/build5/proofs/harness_policy';out.mkdir(exist_ok=True)
source=ast.parse((L/'work/build5/test_runner.py').read_text())
functions=[node for node in source.body if isinstance(node,ast.FunctionDef) and node.name in ('writable','audit')]
scope=dict(Path=Path,os=os,sys=sys,lane=L,output=out,temp_root=L/'work/tmp',denied=[],reserve_probe=False,
           urlsplit=urlsplit,parse_qs=parse_qs,unquote=unquote)
exec(compile(ast.Module(body=functions,type_ignores=[]),'policy-check','exec'),scope)
records=[]
for name,allowed in ((str(out/'a'),True),(str(L/'work/tmp/a'),True),(str(L/'work/tree_r1/a'),False),
                     (str(L/'out/a'),False),('/data3/forbidden',False),('/home/forbidden',False)):
    try:scope['audit']('open',(name,None,os.O_WRONLY|os.O_CREAT));actual=True
    except PermissionError:actual=False
    records.append(dict(path=name,allowed=actual,expected=allowed))
    assert actual==allowed
for args in (('df',['df','-BG','--output=avail','/scratch'],None,None),
             ('python',['python','unexpected.py'],None,None)):
    try:scope['audit']('subprocess.Popen',args);raise AssertionError('Untrusted child admitted')
    except PermissionError:pass
scope['reserve_probe']=True
scope['audit']('subprocess.Popen',('df',['df','-BG','--output=avail','/scratch'],None,None))
(out/'CHECK.json').write_text(json.dumps(dict(writes=records,reserve_probe_only=True),indent=2)+'\n')
print(json.dumps(dict(checked=len(records),passed=True)))
