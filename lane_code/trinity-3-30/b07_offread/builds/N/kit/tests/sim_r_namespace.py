"""Refute R3 naming/namespace: run R's real namespace(root, config) through the installed xnames Popen
mapping with a production-style root (not under /dev/shm), as on Orchard (/tmp/a_<job>_<token>)."""
import json,shutil,subprocess,sys
from pathlib import Path
KIT=Path(sys.argv[1]); root=Path(sys.argv[2])
sys.path.insert(0,str(KIT/'vsi/launcher'))
import xnames as X
import orchard_job as J
tok='a'+'b'*15
pkg=J.physical(root,J.SJ/('a'+tok)/'p')
(pkg/'cohort').mkdir(parents=True,exist_ok=True)
shutil.copy(KIT/'vsi/cohort/MEDIA_MANIFEST.json',pkg/'cohort/MEDIA_MANIFEST.json')
for d in ('sj/uv-python/cpython-3.12.13-linux-x86_64-gnu','fsw','m/ap'):(root/d).mkdir(parents=True,exist_ok=True)
config={'phase_b':False,'spec':{'package':str(J.SJ/('a'+tok)/'p'),'inputs':{'video_root':'/project/community/jjyeung/3e0e8a36'}}}
argv=J.namespace(root,config)
X.install(str(root))
out=subprocess.run(['/bin/echo',*argv[1:]],capture_output=True).stdout.decode().split()
words=('arkitscenes','scannet','av_dataengine_cot')
leaks=sorted({w for a in out for w in words if w in a.lower()})
ap=out[out.index(str(root/'m/ap'))+1]
target=str(J.AP/'19252904/e/bin/python')
sys.__stdout__.write(json.dumps(dict(argv_words_after_mapping=leaks,
  media_binds_with_dataset_word=sum('arkitscenes' in a or 'scannet' in a for a in out),
  media_bind_example=[a for a in out if 'arkitscenes' in a][:1],
  ap_bind_destination_in_namespace=ap,
  vllm_isolated_sh_exec_target=target,
  exec_target_under_bound_ap=target.startswith(ap+'/')),indent=1)+"\n")
