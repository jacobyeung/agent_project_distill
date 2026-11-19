from pathlib import Path
import sys,runpy,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build21d'
p=B/'naming21.py';hits=set();digest=hashlib.sha256(p.read_bytes()).hexdigest()
def trace(frame,event,arg):
    if frame.f_code.co_filename!=str(p):return None
    if event=='line':hits.add(frame.f_lineno)
    return trace
label=sys.argv[1];sys.argv=sys.argv[2:]
sys.settrace(trace)
try:runpy.run_path(str(Path(sys.argv[0]).resolve()),run_name='__main__')
finally:
    sys.settrace(None)
    (D/('TRACE_'+label+'.json')).write_text(json.dumps(dict(sha256=digest,hits=sorted(hits)),indent=2)+'\n')
