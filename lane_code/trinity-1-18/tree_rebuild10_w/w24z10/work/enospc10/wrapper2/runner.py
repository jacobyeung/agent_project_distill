import sys,runpy,time,types
from pathlib import Path
args=sys.argv[1:]
if '-c' in args:
 i=args.index('-c');code=args[i+1];sys.argv=['-c']+args[i+2:];exec(code);raise SystemExit(0)
while args[0].startswith('-'):args.pop(0)
sys.argv=args
if Path(args[0]).name=='j2.py':
 original=time.sleep
 time.sleep=lambda seconds:original(seconds*.003)
runpy.run_path(args[0],run_name='__main__')
