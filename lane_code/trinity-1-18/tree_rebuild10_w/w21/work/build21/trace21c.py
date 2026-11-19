from pathlib import Path
import sys,runpy,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';C=L/'work/build21c'
names=('joblib.py','naming21.py','kit.py')
paths={str(B/n):n for n in names};hits={n:set() for n in names}
hashes={n:hashlib.sha256((B/n).read_bytes()).hexdigest() for n in names}
def trace(frame,event,arg):
    name=paths.get(frame.f_code.co_filename)
    if name is None:return None
    if event=='line':hits[name].add(frame.f_lineno)
    return trace
label=sys.argv[1];script=sys.argv[2];sys.argv=sys.argv[2:]
sys.settrace(trace)
try:runpy.run_path(str(Path(script).resolve()),run_name='__main__')
finally:
    sys.settrace(None)
    value=dict(hits={n:sorted(v) for n,v in hits.items()},sha256=hashes)
    (C/('TRACE_'+label+'.json')).write_text(json.dumps(value,indent=2)+'\n')
