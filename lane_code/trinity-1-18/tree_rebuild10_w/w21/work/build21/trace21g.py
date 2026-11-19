from pathlib import Path
import ast,difflib,hashlib,json,runpy,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21g'
label=sys.argv[1];sys.argv=sys.argv[2:]
paths=[B/'environment21f.py',B/'naming21.py'];sources={str(p):p.read_text() for p in paths};hits={str(p):set() for p in paths}
def trace(frame,event,arg):
    path=frame.f_code.co_filename
    if path not in hits:return None
    if path.endswith('/naming21.py') and frame.f_code.co_name not in ('<module>','scan_decoded','scan_python_environment'):return None
    if event=='line':hits[path].add(frame.f_lineno)
    return trace
sys.settrace(trace)
try:runpy.run_path(sys.argv[0],run_name='__main__')
finally:
    sys.settrace(None);results={}
    for p in paths:
        source=sources[str(p)];assert source==p.read_text()
        statements={n.lineno for n in ast.walk(ast.parse(source)) if isinstance(n,ast.stmt)}
        changed=set();old=(L/'attic/build21g'/p.name).read_text().splitlines()
        for tag,i,j,a,b in difflib.SequenceMatcher(a=old,b=source.splitlines(),autojunk=False).get_opcodes():
            if tag!='equal':changed.update(range(a+1,b+1))
        results[str(p.relative_to(L))]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
            hits=sorted(hits[str(p)]),changed_statements=sorted(changed & statements),
            changed_covered=len(changed & statements & hits[str(p)]),changed_total=len(changed & statements),
            changed_missing=sorted(changed & statements-hits[str(p)]))
    (D/('TRACE_'+label+'.json')).write_text(json.dumps(results,indent=2)+'\n')
