"""Interpreter front end: template venv plus the pinned overlay in d/v/site (appended, base wins)."""
import runpy
import site
import sys

args = sys.argv[1:]
while args and args[0] in ('-B', '-I', '-s', '-E'):
    args.pop(0)
if not args or args[0].startswith('-'):
    raise SystemExit('boot.py runs a script path only')
site.addsitedir('/scratch/jjyeung/b01ec87a6f29b/d/v/site')
sys.argv = args
runpy.run_path(args[0], run_name='__main__')
