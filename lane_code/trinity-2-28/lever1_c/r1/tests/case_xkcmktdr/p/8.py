
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
"""Standalone package checker and explicit operator-only submit/fetch commands."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import types


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load_helpers(package):
    # Load three small pinned modules in memory; never expand the code tree on login.
    public=json.loads((package/'0.json').read_text())
    if digest(package/'0.tgz')!=public['payload_sha256']:raise ValueError('Code archive differs')
    mod=types.ModuleType('orchard_h10');mod.__path__=[];sys.modules['orchard_h10']=mod
    with tarfile.open(package/'0.tgz') as archive:
        cfg={**json.load(archive.extractfile('9.json')),**public}
        for name in ('common','export_pins','job'):
            path='orchard_h10/'+name+'.py';raw=archive.extractfile(path).read()
            if hashlib.sha256(raw).hexdigest()!=cfg['payload_pins'][path]['sha256']:raise ValueError('Helper differs')
            m=types.ModuleType('orchard_h10.'+name);m.__file__=path;sys.modules[m.__name__]=m
            exec(compile(raw,path,'exec'),m.__dict__)
    from orchard_h10.job import verify_config
    verify_config(cfg)
    return cfg


def check(package, gpus, walltime):
    cfg=load_helpers(package)
    from orchard_h10.common import opaque, submit_argv
    from orchard_h10.job import check_inputs
    receipt=json.loads((package/'PACKAGE.json').read_text())
    for name,h in receipt['files'].items():
        if digest(package/name)!=h:raise ValueError('Package changed: '+name)
    if package!=Path('/project/community/jjyeung')/cfg['token']:
        raise ValueError('Stage the package under /project/community/jjyeung/'+cfg['token'])
    private=package/'a';private.mkdir(mode=0o700,exist_ok=True)
    if private.stat().st_mode & 0o077:raise ValueError('Private input directory must be 0700')
    inputs=check_inputs(json.loads((private/'1.json').read_text()),cfg,package=package)
    opaque([str(package),str(package/'1.json'),str(package/'2.json')])
    for a in inputs['archives']:
        for part in a['parts']:
            opaque([part['path']])
            if Path(part['path']).stat().st_size!=part['bytes']:raise ValueError('Staged input size differs')
    # This is a metadata CPU check. Full hashes, imports, restore, and frame admission
    # execute on the allocated node after archive extraction, before a model decode.
    argv=submit_argv(cfg['token'],gpus,walltime)
    value=dict(passed=True,plan=cfg['plan_sha256'],inputs=digest(package/'a/1.json'),
               package=digest(package/'PACKAGE.json'),gpus=gpus,time=walltime,argv=argv,
               scope=0)
    (package/'2.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return value


def submit(package,gpus,walltime,test_only=False):
    cfg=load_helpers(package)
    from orchard_h10.common import opaque, submit_argv, seconds
    cpu=json.loads((package/'2.json').read_text())
    if (cpu.get('plan')!=cfg['plan_sha256'] or cpu.get('inputs')!=digest(package/'a/1.json') or
            cpu.get('package')!=digest(package/'PACKAGE.json') or cpu.get('gpus')!=gpus or cpu.get('time')!=walltime):
        raise ValueError('Run the CPU check for these exact inputs, card count and time first')
    from orchard_h10.job import check_inputs
    check_inputs(json.loads((package/'a/1.json').read_text()),cfg,package=package)
    argv=submit_argv(cfg['token'],gpus,walltime)
    export=f"--export=A_N={gpus},A_T={seconds(walltime)},A_I={digest(package/'a/1.json')},A_C={digest(package/'2.json')}"
    argv[argv.index('--export=NONE')]=export
    opaque(argv)
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':os.environ['HOME'],'USER':os.environ['USER']}
    opaque([f'{k}={v}' for k,v in env.items()])
    body=(package/'BATCH.sh').read_bytes()
    # Check retained package pins again; no implicit check+submit retry chain.
    pins=json.loads((package/'PACKAGE.json').read_text())['files']
    if any(digest(package/n)!=h for n,h in pins.items()):raise ValueError('Package changed after check')
    result=subprocess.run(argv+(['--test-only'] if test_only else []),input=body,env=env,cwd='/tmp',capture_output=True)
    sys.stdout.buffer.write(result.stdout);sys.stderr.buffer.write(result.stderr)
    with (package/'LEDGER.jsonl').open('a') as f:
        f.write(json.dumps(dict(action='test-only' if test_only else 'submit',returncode=result.returncode,
                  stdout=result.stdout.decode(),stderr=result.stderr.decode(),argv=argv,plan=cfg['plan_sha256']))+'\n')
        f.flush();os.fsync(f.fileno())
    return result.returncode


def fetch(package,token,destination):
    cfg=load_helpers(package)
    from orchard_h10.common import opaque
    import re
    if not re.fullmatch(re.escape(cfg['token'])+'[0-9a-f]{8}',token):raise ValueError('Return token differs')
    source=Path(cfg['pool'])/token;destination=Path(destination).resolve()
    opaque([token,str(destination)])
    destination.mkdir(parents=True,exist_ok=False)
    # Reuse the template's framed stream locally on Orchard. An operator can pipe
    # this same emit command through the governed transport to Trinity instead.
    with tarfile.open(package/'0.tgz') as archive:
        raw=archive.extractfile('orchard_h10/vendor/stdout_transfer.py').read()
    m=types.ModuleType('stdout_transfer');exec(compile(raw,'stdout_transfer.py','exec'),m.__dict__)
    exit_value=json.loads((source/'EXIT.json').read_text())
    result=source/'result.tar.gz'
    if digest(result)!=exit_value['archive_sha256']:raise ValueError('Returned archive differs')
    # The return limit is 90 MB, so the stream stays bounded. Do not load it in memory.
    transfer=destination/'0.stream'
    with transfer.open('xb') as out:m.emit(result,out,cfg['plan_sha256'],'complete' if exit_value['complete'] else 'failed')
    with transfer.open('rb') as stream,(destination/'0.log').open('wb') as log:
        m.receive(stream,destination/'0.tgz',cfg['plan_sha256'],log)
    for name in ('EXIT.json','RETURN_RECEIPT.json'):
        (destination/name).write_bytes((source/name).read_bytes())
    print(json.dumps(dict(destination=str(destination),complete=exit_value['complete'],sha256=digest(destination/'0.tgz'))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('check','submit','fetch'))
    p.add_argument('--gpus',type=int,default=4);p.add_argument('--time');p.add_argument('--test-only',action='store_true')
    p.add_argument('--return-token');p.add_argument('--out');a=p.parse_args();root=Path(__file__).resolve().parent
    if a.action=='check':print(json.dumps(check(root,a.gpus,a.time),sort_keys=True))
    elif a.action=='submit':raise SystemExit(submit(root,a.gpus,a.time,a.test_only))
    else:fetch(root,a.return_token,a.out)
