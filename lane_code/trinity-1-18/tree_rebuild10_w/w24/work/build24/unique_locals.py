"""Keep runtime environment inputs syntactically independent of resolver locals."""
from pathlib import Path
import ast,io,tokenize
L=Path(__file__).resolve().parents[2];p=L/'work/build24/joblib.py';source=p.read_text();tree=ast.parse(source)
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bootstrap')
names={n.id for n in ast.walk(f) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)}
names.update(a.arg for a in f.args.args)
names.discard('env')
mapping={n:'boot_'+n for n in names}
tokens=[]
for token in tokenize.generate_tokens(io.StringIO(source).readline):
    if f.lineno<=token.start[0]<=f.end_lineno and token.type==tokenize.NAME and token.string in mapping:
        token=token._replace(string=mapping[token.string])
    tokens.append(token)
p.write_text(tokenize.untokenize(tokens))
print('Renamed bootstrap locals:',sorted(mapping))
