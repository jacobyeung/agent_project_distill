# Build the fixed kit as a new folder from the reviewed one (usage: patch4.py <old kit> <new kit> <src>):
#  1. b/mg.py answers the device queries only while the library is not initialized;
#  2. the forward runs in-process as the tree runs it: a.py leaves production_proof.forward alone, and
#     b/fw.py is not copied into the new kit;
#  3. a.py appends the unscreened traceback of every exception its wrappers see, and of the exception
#     that ends production_proof._run in a refusal, to <parent of argv[2]>/tb.txt, bounded at 200 KB.
import sys,hashlib,os,shutil
from pathlib import Path
K0=Path(sys.argv[1]).resolve();K=Path(sys.argv[2]).resolve();src=Path(sys.argv[3])
assert not K.exists()
def skip(folder,names):
    return [n for n in names if n=='__pycache__' or (Path(folder).resolve()==K0/'b' and n=='fw.py')]
shutil.copytree(K0,K,ignore=skip,copy_function=shutil.copy2)
for d in [K0,*[p for p in K0.rglob('*') if p.is_dir() and p.name!='__pycache__']]:
    os.chmod(K/d.relative_to(K0),os.stat(d).st_mode&0o7777)
def swap(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)
a=K/'b/a.py';s=a.read_text()
s=swap(s,'''root.mkdir(parents=True,mode=0o700,exist_ok=True)
if sys.argv[1] in ('q','r'):
 import os
 sys.path.insert(0,str(kit/'b'))
 from z import screen,write,load
 def refused(kind,value,traceback):
  text=screen(''','''root.mkdir(parents=True,mode=0o700,exist_ok=True)
def tb_write(where,error):return None
if sys.argv[1] in ('q','r'):
 import os
 sys.path.insert(0,str(kit/'b'))
 from z import screen,write,load
 def tb_write(where,error):
  # Append the full, unscreened traceback of an exception to the node-local file beside r.json:
  # once per exception, at most 65536 bytes a record and 204800 bytes in all. Never raises.
  try:
   import time,traceback
   if getattr(error,'_tb_written',False):return None
   try:error._tb_written=True
   except Exception:pass
   text='=== %s pid=%d where=%s %s\\n'%(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),os.getpid(),where,type(error).__name__)
   text+='Stack above the wrapper:\\n'+''.join(traceback.format_stack()[:-1])
   text+=''.join(traceback.format_exception(type(error),error,error.__traceback__))+'\\n'
   data=text.encode('utf-8','replace')
   if len(data)>65536:data=data[:16384]+data[-49152:]
   path=root.parent/'tb.txt'
   room=204800-(path.stat().st_size if path.exists() else 0)
   if room>0:
    descriptor=os.open(path,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
    try:os.write(descriptor,data[:room])
    finally:os.close(descriptor)
  except Exception:pass
  return None
 def refused(kind,value,traceback):
  tb_write('uncaught',value)
  text=screen(''')
s=swap(s,''' from rb import routing_status
 routing_status(cfg)
 return original_selection(cfg, directory, request, result, record=record)
''',''' try:
  from rb import routing_status
  routing_status(cfg)
  return original_selection(cfg, directory, request, result, record=record)
 except BaseException as error:tb_write('selection',error);raise
''')
s=swap(s,''' result = original_host(cfg, directory, request, job_tmp_token=job_tmp_token)
 host_write(root/'host.json',result)
 return result
''',''' try:
  result = original_host(cfg, directory, request, job_tmp_token=job_tmp_token)
  host_write(root/'host.json',result)
  return result
 except BaseException as error:tb_write('host',error);raise
''')
s=swap(s,'''    # A driver query made while admit() hides the devices would leave this process unable to open
    # one later; b/mg.py answers the device queries without the driver for as long as the mask is empty.
    from mg import guard
    def restoring_admit(*args,**kwargs):
     limit=resource.getrlimit(resource.RLIMIT_AS)
     try:
      with guard():return native_admit(*args,**kwargs)
     finally:resource.setrlimit(resource.RLIMIT_AS,limit)
    admission_module.admit=restoring_admit
    # A device query made while admit() hides the devices leaves this process unable to open one
    # later, so the forward runs in a fresh interpreter (b/fw.py) with the job's limit and scopes.
    import launch_r1.production_proof as proof_module
    from fw import call
    job_limit=resource.getrlimit(resource.RLIMIT_AS)
    def spawned_forward(*args,**kwargs):
     return call('launch_r1.production_proof','forward',args,kwargs,limit=job_limit)
    proof_module.forward=spawned_forward
''','''    # A driver query made while admit() hides the devices would leave a process that has not opened
    # a device unable to open one later; b/mg.py answers the device queries without the driver while
    # the mask is empty and the library is not initialized. A process that opened a device before the
    # mask keeps it under the mask, and there the library's own functions answer.
    from mg import guard
    def restoring_admit(*args,**kwargs):
     limit=resource.getrlimit(resource.RLIMIT_AS)
     try:
      with guard():return native_admit(*args,**kwargs)
     except BaseException as error:tb_write('admit',error);raise
     finally:resource.setrlimit(resource.RLIMIT_AS,limit)
    admission_module.admit=restoring_admit
    # The forward runs in this process, as the tree runs it. _run turns the exception of any step
    # into its refusal text with str(error); this name records that exception's traceback first.
    import launch_r1.production_proof as proof_module
    def refusal_text(*args,**kwargs):
     if args and isinstance(args[0],BaseException):tb_write('refusal',args[0])
     return str(*args,**kwargs)
    proof_module.str=refusal_text
''')
a.write_text(s)
mode=os.stat(K/'b/z.py').st_mode&0o7777
m=K/'b/mg.py';assert m.exists();m.write_bytes((src/'mg.py').read_bytes());os.chmod(m,mode)
assert not (K/'b/fw.py').exists() and (K0/'b/fw.py').exists()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
L=(K/'SHA256SUMS.txt').read_text().splitlines()
name=lambda l:l.split('  ',1)[1]
assert [name(l) for l in L]==sorted(name(l) for l in L)
assert sum(name(l)=='b/fw.py' for l in L)==1
new={'b/a.py':a,'b/mg.py':m}
L=[(sha(new[name(l)])+'  '+name(l)) if name(l) in new else l for l in L if name(l)!='b/fw.py']
(K/'SHA256SUMS.txt').write_text('\n'.join(L)+'\n')
print({n:sha(K/n)[:16] for n in ('b/a.py','b/mg.py')},'seal',sha(K/'SHA256SUMS.txt'))
