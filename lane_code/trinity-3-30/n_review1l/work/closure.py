import sys, ast
from pathlib import Path, PurePath
def _irt(self,other):
    try: self.relative_to(other); return True
    except ValueError: return False
PurePath.is_relative_to=_irt
root=Path(sys.argv[1]).resolve()
src=(root/'student_pilot/p3_provenance.py').read_text()
mod=ast.parse(src)
fn=[n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name=='source_files'][0]
ns={'Path':Path}
code=ast.Module(body=[fn],type_ignores=[])
exec(compile(code,'sf','exec'),ns)
# root inside function is Path(__file__).parent -> patch by setting __file__
ns['__file__']=str(root/'student_pilot/p3_provenance.py')
exec(compile(code,str(root/'student_pilot/p3_provenance.py'),'exec'),ns)
files=ns['source_files']([root/'student_pilot/s1_pool.py'])
rel=sorted(str(p.relative_to(root)) for p in files)
print(len(rel))
for t in sys.argv[2:]: print(t, t in rel)
