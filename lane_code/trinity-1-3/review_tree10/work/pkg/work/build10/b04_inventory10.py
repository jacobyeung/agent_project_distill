from pathlib import Path
import ast,hashlib,json
B=Path(__file__).resolve().parent;root=B/'b04_stage';rows=[];hashes={}
for file in sorted(root.rglob('*.py')):
    name=str(file.relative_to(root));raw=file.read_bytes();hashes[name]=hashlib.sha256(raw).hexdigest()
    def visit(nodes,prefix=''):
        for node in nodes:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                symbol=prefix+node.name
                if not isinstance(node,ast.ClassDef):rows.append(dict(file=name,line=node.lineno,component=symbol))
                visit(node.body,symbol+'.')
            elif not prefix and isinstance(node,(ast.Assign,ast.AnnAssign)) and isinstance(node.value,(ast.Constant,ast.Dict,ast.List,ast.Tuple)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target,ast.Name):rows.append(dict(file=name,line=node.lineno,component=target.id))
    visit(ast.parse(raw).body)
value=dict(scope='Every staged b04 Python file; conservative inventory includes fixture and training support, not a proven deployed path.',source_hashes=hashes,components=rows)
(B/'proofs/audit/B04_COMPONENTS.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'files':len(hashes),'components':len(rows)}))
