"""Rebind an existing bound input bundle to this reviewed source tree, into a new stage."""
import argparse,ast,hashlib,io,json,re,secrets,sys,tarfile
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT,AWS,archive,save,sha
sys.path.insert(0,str(ROOT/'evaluator'))
from cells import frame_count,REVSI_PINNED_ADMISSION


def rebind(source, target, *, until=None, remote_root=None, build_only=False):
    source,target=Path(source).resolve(),Path(target).resolve()
    if target.exists() or not target.is_relative_to(ROOT.resolve()):
        raise ValueError('Rebind requires a new stage inside this source kit')
    # Root transport seals may describe an earlier binding. Authenticate the
    # current request content, evaluator archive, and every embedded input pin.
    blobs={}
    with tarfile.open(source/'k/1.tar') as tf:
        for member in tf.getmembers():
            rel=Path(member.name)
            if not member.isfile() or rel.is_absolute() or '..' in rel.parts or member.size>8*1024*1024:
                raise ValueError('Unsafe input bundle member')
            blobs[member.name]=tf.extractfile(member).read()
    cfg=json.loads(blobs['0.json'])
    auth=json.loads((source/'k/2.json').read_text())
    content={k:v for k,v in cfg.items() if k not in ('binding','output')}
    if hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()!=cfg['binding'] and 'until' in content:
        if cfg['until']!=auth['until']:raise ValueError('Legacy deadline differs from authorization')
        # Original aws_eval_gaps appended until after hashing the request.
        content.pop('until')
    if hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()!=cfg['binding'] or cfg['source_sha256']!=sha(source/'k/0.tar'):
        raise ValueError('Bound request binding/source differs')
    def check_pins(value):
        if isinstance(value,dict):
            path=value.get('path','')
            if isinstance(path,str) and path.startswith('$Q/'):
                if path[3:] not in blobs or hashlib.sha256(blobs[path[3:]]).hexdigest()!=value.get('sha256'):
                    raise ValueError('Embedded input pin differs')
            for child in value.values():check_pins(child)
        elif isinstance(value,list):
            for child in value:check_pins(child)
    check_pins(cfg)
    if cfg.get('unbound'):raise ValueError('Unbound request cannot be adopted')
    for cell in cfg['cells']:
        frame_count(cell)
        if (ROOT/'evaluator/think_settings.py').exists():
            from think_settings import validate
            validate(cell)
            if cell['benchmarks']!=['revsi']:raise ValueError('Thinking fork requires ReVSI only')
        elif not REVSI_PINNED_ADMISSION and 'revsi' in cell['benchmarks']:
            raise ValueError('ReVSI requires a kit with pinned-tier admission')
    auth=json.loads((source/'k/2.json').read_text())
    if auth['request_sha256']!=sha(source/'k/1.tar'):raise ValueError('Bound metadata archive hash differs')
    if cfg['gpus']!=auth['gpus'] or cfg['gpus']+auth['other_gpus']>auth['gpu_cap']:
        raise ValueError('Original GPU authorization differs')
    new_root=remote_root or AWS+'/ap/'+secrets.token_hex(4)
    if not re.fullmatch(re.escape(AWS)+r'/ap/[0-9a-f]{8}',new_root) or new_root==auth['root']:
        raise ValueError('Require a fresh opaque deployment root')
    if build_only:until='2000-01-01T00:00:00Z'
    else:
        if not until:raise ValueError('Require a fresh UTC deadline')
        delta=(datetime.fromisoformat(until.replace('Z','+00:00'))-datetime.now(timezone.utc)).total_seconds()
        if not 300<delta<=14400:raise ValueError('Deadline must be 5 minutes to 4 hours away')
    code={}
    for directory in (ROOT/'evaluator',ROOT/'evaluator/evalpath',ROOT/'evaluator/trainer'):
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix in ('.py','.json'):
                code[str(path.relative_to(ROOT/'evaluator'))]=path.read_bytes()
    for i,path in enumerate(sorted((ROOT/'inputs/trainer_sources').iterdir())):
        code['audit/'+str(i)+'.py']=path.read_bytes()
    code['audit/0.json']=(ROOT/'inputs/SOURCE_PINS.json').read_bytes()
    adapter=ROOT/'inputs/TRAINER_ADAPTER.json'
    if adapter.exists():code['audit/TRAINER_ADAPTER.json']=adapter.read_bytes()
    archive(target/'kit/k/0.tar',code)
    cfg.update(source_sha256=sha(target/'kit/k/0.tar'),build_only=build_only)
    if 'until' in cfg:cfg['until']=until
    cfg.pop('binding');cfg.pop('output')
    cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    cfg['output']=new_root+'/o/'+cfg['binding'][:24]
    blobs['0.json']=(json.dumps(cfg,sort_keys=True)+'\n').encode()
    archive(target/'kit/k/1.tar',blobs)
    auth.update(root=new_root,until=until,build_only=build_only,request_sha256=sha(target/'kit/k/1.tar'))
    save(target/'kit/k/2.json',auth)
    # Use this kit's reviewed launcher template; never inherit an old script.
    tree=ast.parse((ROOT/'local/bind_vl.py').read_text())
    script=next(n.value.value for n in ast.walk(tree) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='script' for t in n.targets)
        and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))
    name='a15_cot_ap'+secrets.token_hex(4)
    for old,new in [('NAME',name),('COUNT',str(cfg['gpus'])),('MEM',str(cfg['gpus']*80)),('REMOTE',new_root),('OPAQUE',new_root.rsplit('/',1)[-1])]:
        script=script.replace(old,new)
    (target/'kit/b').mkdir(parents=True)
    (target/'kit/b/0.sh').write_text(script)
    (target/'kit/b/1.py').write_bytes((ROOT/'kit/b/1.py').read_bytes())
    save(target/'inputs/REQUEST.json',cfg)
    save(target/'DESTINATIONS.json',dict(root=new_root,output=cfg['output']))
    save(target/'JOBS.json',dict(name=name,script='b/0.sh',gpus=cfg['gpus']))
    return cfg


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bound-kit',required=True,type=Path)
    p.add_argument('--artifact-dir',required=True,type=Path)
    p.add_argument('--until');p.add_argument('--remote-root');p.add_argument('--build-only',action='store_true')
    a=p.parse_args();cfg=rebind(a.bound_kit,a.artifact_dir,until=a.until,remote_root=a.remote_root,build_only=a.build_only)
    print(json.dumps(dict(binding=cfg['binding'],source_sha256=cfg['source_sha256'],output=cfg['output'],build_only=cfg['build_only'])))

if __name__=='__main__':main()
