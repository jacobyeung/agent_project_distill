from pathlib import Path
import ast,difflib,hashlib,json,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build22';T=L/'work/tree_r1';old=L.parent/'w21/work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
files=inventory(T);changed={};patch=[]
for name,h in files.items():
    p=T/name;q=old/name;raw=q.read_bytes() if q.is_file() else b''
    before=hashlib.sha256(raw).hexdigest() if q.is_file() else None
    if before==h:continue
    value=dict(before=before,after=h)
    if p.suffix=='.py':
        a=raw.decode().splitlines();b=p.read_text().splitlines();lines=set()
        for tag,i,j,k,m in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
            if tag!='equal':lines.update(range(k+1,m+1))
        statements={n.lineno for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.stmt)}
        value['changed_statements']=sorted(lines&statements)
        patch.extend(difflib.unified_diff(a,b,fromfile='build21/'+name,tofile='build22/'+name,lineterm=''))
    changed[name]=value
(D/'TREE_CHANGES.json').write_text(json.dumps(changed,indent=2)+'\n')
(D/'TREE_CHANGES.diff').write_text('\n'.join(patch)+'\n')
(D/'TREE_FILES.json').write_text(json.dumps(files,sort_keys=True,indent=2)+'\n')
seal=dict(tree_sha256=digest(files),files=len(files))
(L/'out/TREE_SEAL.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps(seal),len(changed),'changed files')
