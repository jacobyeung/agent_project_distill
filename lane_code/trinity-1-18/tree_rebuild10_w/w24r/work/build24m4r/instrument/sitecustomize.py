import atexit,errno,json,os,sys
from pathlib import Path
calls=[]
def profile(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='compare' and frame.f_code.co_filename.endswith('/s1_scene_census.py'):
  calls.append(dict(source=frame.f_locals['source'],result=arg))
sys.setprofile(profile)
def finish():
 sys.setprofile(None)
 q=Path('/tmp/q_22c714e1/z/q')
 tests={}
 for label,p in [('tree',Path('/tmp/q_22c714e1/z/s/a')),('input',Path('/tmp/q_22c714e1/z/i/a')),('output_alias',Path('/tmp/q_22c714e1/z/i/sc/a')),('other_tmp',Path('/tmp/q_22c714e1/u/a')),('root',Path('/a'))]:
  try:p.write_text('bad')
  except OSError as e:
   tests[label]=e.errno
   assert e.errno==errno.EROFS,(label,e)
  else:raise AssertionError(label)
 (q/'access.json').write_text(json.dumps(dict(compare_calls=calls,readonly=tests,dev=Path('/dev/null').exists(),proc=Path('/proc/self/maps').is_file())))
atexit.register(finish)
