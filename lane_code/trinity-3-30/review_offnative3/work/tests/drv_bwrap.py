"""Run the shipped R launcher's namespace through installed xnames and the real bwrap.
argv: kit_launcher_dir root out_json. The root already holds the extracted bootstrap bundle."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
launcher,root,out=sys.argv[1],sys.argv[2],sys.argv[3]
sys.path.insert(0,root+'/bootstrap')
import xnames as X
X.install(root)                      # same call trace_runtime.py makes before orchard_job is imported
import orchard_job as J, orchard_stage as S
config=json.loads(Path(root+'/bootstrap/CONFIG.json').read_text())
aliases_before=len(X._ALIASES)
with open(root+'/bootstrap/payload.tar.gz','rb') as s:S.extract_stream(s,root,None,32*1024**2,overlay=True)
R=Path(root)
for d in ('fsw','sj/uv-python'):(R/d).mkdir(parents=True,exist_ok=True)
os.symlink('/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu',str(R/'sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'))
(R/'m/ap/19252904/e/bin').mkdir(parents=True)
os.symlink(S.RUNTIME_ABSOLUTE_LINKS['m/ap/19252904/e/bin/python'],str(R/'m/ap/19252904/e/bin/python'))
shutil.copy('/usr/bin/bwrap',str(R/'bwrap'))
package=J.physical(R,config['spec']['package'])
rows=json.loads((package/'cohort/MEDIA_MANIFEST.json').read_text())
(R/'v').mkdir()
for r in rows:(R/'v'/(r['sha256']+'.mp4')).write_bytes(r['sha256'].encode())
probe=R/'bootstrap/zz.py'
probe.write_text('''import json,os,sys
from pathlib import Path
rows=json.loads(Path(sys.argv[1]).read_text())
logical=sys.argv[2]+'/'+rows[0]['relative_path']
media_ok=open(logical,'rb').read()==rows[0]['sha256'].encode()
ppid=os.getppid()
rec=dict(executable=sys.executable,cwd=os.getcwd(),media_ok=media_ok,
  parent_cmdline=open('/proc/%d/cmdline'%ppid,'rb').read().decode(errors='replace').split(chr(0)),
  self_cmdline=open('/proc/self/cmdline','rb').read().decode(errors='replace').split(chr(0)))
open(sys.argv[3],'w').write(json.dumps(rec))
''')
result=R/'PROBE.json'
command=J.namespace(R,config)+[config['spec']['interpreters']['vllm'],'-s','-B',str(R/'bootstrap/trace_runtime.py'),
   '--script',str(probe),'--root',str(R),'--config',str(R/'bootstrap/CONFIG.json'),
   str(package/'cohort/MEDIA_MANIFEST.json'),config['spec']['inputs']['video_root'],str(result)]
env=J.environment(R)
p=subprocess.Popen(command,env=env,cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
time.sleep(0.3)
try:outer=open('/proc/%d/cmdline'%p.pid,'rb').read().decode(errors='replace').split('\0')
except OSError:outer=None
log=p.communicate(timeout=120)[0]
probe_rec=json.loads(result.read_text()) if result.is_file() else None
sh=(package/'vllm_isolated.sh').read_text()
sys.__stdout__.write(json.dumps(dict(rc=p.returncode,log=log.decode(errors='replace')[-3000:],probe=probe_rec,
   outer_cmdline=outer,vllm_sh=sh,ap=str(J.AP),aliases_before_namespace=aliases_before,media=len(rows)))+'\n')
