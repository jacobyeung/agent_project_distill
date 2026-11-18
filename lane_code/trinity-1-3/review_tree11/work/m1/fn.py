import ast,sys,hashlib
for t in sys.argv[2:]:
    src=open(t+'/student_pilot/carrier_c1_run.py').read(); m=ast.parse(src)
    for n in m.body:
        if isinstance(n,ast.FunctionDef) and n.name==sys.argv[1]:
            seg=ast.get_source_segment(src,n); print(n.lineno,n.end_lineno,hashlib.sha256(seg.encode()).hexdigest()[:16],t[-45:])
