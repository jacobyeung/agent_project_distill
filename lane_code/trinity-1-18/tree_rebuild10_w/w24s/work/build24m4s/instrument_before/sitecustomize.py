import atexit,errno,json,os,sys
from pathlib import Path
calls=[]
def profile(frame,event,arg):
 if event=='return' and frame.f_code.co_name=='compare' and frame.f_code.co_filename.endswith('/s1_scene_census.py'):
  calls.append(dict(source=frame.f_locals['source'],result=arg))
sys.setprofile(profile)
def finish():
 sys.setprofile(None)
 if not calls:return
 z=Path('/tmp/q_22c714e1')/('p' if os.environ.get('FIX_MODE')=='q' else 'z')
 tests={}
 paths=[('tree',Path(os.environ['FIX_SOURCE'])/'a'),('input',z/'i/a'),('output_alias',z/'i/sc/a'),('root',Path('/a')),('kit',Path(os.environ['FIX_KIT'])/'a'),('cl',Path(os.environ['ANYHOST_JOBS'])/'a'),('alias',Path(os.environ['ANYHOST_JOBS'])/'site_alias/a')]
 value=json.loads((z/'i/value.json').read_text())
 paths.extend(('source'+str(i),Path(p)) for i,p in enumerate(sorted(set(value['paths'].values()))))
 for label,p in paths:
  try:
   with p.open('ab'):pass
  except OSError as e:
   tests[label]=e.errno
   assert e.errno==errno.EROFS,(label,e)
  else:raise AssertionError(label)
 import student_pilot
 assert Path(student_pilot.__file__).resolve().parent.parent==Path(os.environ['FIX_SOURCE']).resolve()
 (z/'q/access.json').write_text(json.dumps(dict(compare_calls=calls,readonly=tests,dev=Path('/dev/null').exists(),proc=Path('/proc/self/maps').is_file(),trainer=student_pilot.__file__)))
atexit.register(finish)
