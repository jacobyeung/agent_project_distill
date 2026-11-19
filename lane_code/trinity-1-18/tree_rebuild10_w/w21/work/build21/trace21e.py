from pathlib import Path
import sys,runpy,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21e'
paths=[B/'joblib.py',B/'kit.py'];hits={str(p):set() for p in paths};hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
def trace(frame,event,arg):
    if frame.f_code.co_filename not in hits:return None
    if event=='line':hits[frame.f_code.co_filename].add(frame.f_lineno)
    return trace
label=sys.argv[1];sys.argv=sys.argv[2:];sys.settrace(trace)
try:runpy.run_path(str(Path(sys.argv[0]).resolve()),run_name='__main__')
finally:
    sys.settrace(None)
    (D/('TRACE_'+label+'.json')).write_text(json.dumps({str(Path(p).relative_to(L)):dict(sha256=hashes[p],hits=sorted(v)) for p,v in hits.items()},indent=2)+'\n')
