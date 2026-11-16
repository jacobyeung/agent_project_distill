"""Run the full CPU worker with the production path mapper on local disk."""
from pathlib import Path
import json,os,subprocess,sys
from offnative.paths import ROOT,OFFKIT
from offnative.portable import sources,ROOTS
from offnative.opacity import pack,path_name

def main():
    destination=Path(sys.argv[1])
    assert __import__('re').fullmatch(r'/tmp/a_900000_[0-9a-f]{12}',str(destination))
    ram=Path(os.environ['A0_FIXTURE_RAM'])
    destination.mkdir();ram.mkdir()
    files,_=sources();python_names={path_name(n) for n in files if n.endswith('.py')}
    files['r.json']=json.dumps(ROOTS).encode()
    files['xnames.py']=(ROOT/'offnative/opacity.py').read_bytes();python_names.add('xnames.py')
    files,pins=pack(files);files['out/ARCHIVE_TRANSPORT.json']=json.dumps(pins).encode()
    source_bytes=0
    for i,(name,raw) in enumerate(files.items()):
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        if name in python_names or name in ('r.json','x0.json'):
            target.write_bytes(raw)
            source_bytes+=len(raw)
        else:
            asset=ram/str(i);asset.write_bytes(raw);target.symlink_to(asset)
    code=r'''import os,sys,json,shlex,subprocess
from pathlib import Path
# External CPU libraries and owner offkit remain read-only fixture dependencies.
import av,torch
from transformers import Qwen3Config,Qwen3ForCausalLM
import offkit.bind,offkit.report,offkit.frames
import xnames as X
base=Path(offkit.__file__).parent
fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
for p in [base,*base.glob('*.py')]:X.media_alias(str(p),'/proc/'+str(os.getpid())+'/fd/'+str(fd)+'/'+str(p.relative_to(base)))
held=[]
for module in list(sys.modules.values()):
    name=getattr(module,'__file__',None)
    if name and name.startswith(sys.prefix+'/') and X._BAD.search(name) and Path(name).is_file():
        handle=os.open(name,os.O_RDONLY);held.append(handle)
        X.media_alias(name,'/proc/'+str(os.getpid())+'/fd/'+str(handle))
X.install('.')
from offnative.rehearse import run
import offnative.worker as W
original_journal=W.journal
trace_path=Path(os.environ['A0_TRACE'])
def journal(path,row):
    path=Path(path)
    if path.name=='decode.jsonl' and not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(trace_path)
    return original_journal(path,row)
W.journal=journal
run('work/result','harness',benchmark='vsibench5130')
from offnative.paths import r_launcher
R=r_launcher();L=R.launcher('revsi999t32')
config=L.prepare('a0123456789',Path('work/p0'),mode='production',media_root='/project/community/jjyeung/okh7/313db5a47f11ff0c',phase_b=False)
root=Path.cwd()/'work/ns';root.mkdir()
argv=L.J.namespace(root)
mapped=subprocess.run(['/bin/echo',*argv],capture_output=True,text=True,check=True).stdout.split()
for arg in mapped:X.scan(arg)
payload=R.unpack(R.boot_files(Path('work/p0/BATCH.sh'))['bootstrap/payload.tar.gz'])
shell=next(v for k,v in payload.items() if k.endswith('/vllm_isolated.sh')).decode()
target=shlex.split(shell.splitlines()[1])[1]
assert target.startswith(str(L.J.AP)+'/') and str(L.J.AP) in mapped
from offnative.io import dump
dump('work/NAMESPACE.json',dict(passed=True,non_ram_branch=True,argv=mapped,exec_target=target))
'''
    env=dict(os.environ,PYTHONPATH=str(OFFKIT),A0_ROOTS='r.json',A0_TRACE=str(ram/'decode.jsonl'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    with (ram/'execution.log').open('w') as log:
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=destination,env=env,stdout=log,stderr=log)
    total=sum(p.lstat().st_size for p in destination.rglob('*') if p.is_file() or p.is_symlink())
    record=dict(path=str(destination),ram_assets=str(ram),returncode=result.returncode,nonshm_bytes=total,python_bytes=source_bytes,limit_bytes=20_000_000)
    (ram/'CHECK.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
    assert total<20_000_000
    assert result.returncode==0,(ram/'execution.log').read_text()[-3000:]
if __name__=='__main__':main()
