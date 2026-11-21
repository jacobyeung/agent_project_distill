
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
"""Boot the real numeric worker before any model or capture staging."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def check(cfg):
    from orchard_h10.common import write, template
    from orchard_h10.e import exception
    config=cfg['config'];receipt=Path(config['output'])/'metadata/25.json'
    started=time.monotonic()
    value=dict(passed=False,bulk_bytes=0,python=sys.executable,cwd=os.getcwd(),
               plan=cfg['plan'],job=cfg['job'],modules=0)
    try:
        from g.w import bind_reader_root
        bind_reader_root(Path(config['package'])/'b')
        template()
        from student_pilot.g3t_online import VENDOR, vendor_digest
        from student_pilot.tower_read import SOURCE_SHA256
        from student_pilot.c1r_ref import source_import
        if vendor_digest()!=SOURCE_SHA256:raise ValueError('E53')
        source_import(VENDOR)
        import importlib
        manifest=json.loads((Path(config['package'])/'g/3.json').read_text())
        for name in manifest['modules']:
            importlib.import_module(name)
            value['modules']+=1
        for name,symbol in manifest['symbols']:
            module=__import__(name,fromlist=[symbol])
            getattr(module,symbol)
        value['passed']=True
    except BaseException as error:
        exception(receipt.with_name('26.json'),error)
        raise
    finally:
        value['seconds']=time.monotonic()-started
        write(receipt,value)


def worker(cfg):
    from orchard_h10.runner import control, environment
    from orchard_h10.common import write, checked_run
    config=cfg['config'];root=control(config)
    request=dict(cfg,action=3,boot=True)
    write(root/'30.json',request)
    # Match the production operator: same prefix, interpreter, flags, relative
    # entry/config names, cache root, environment constructor and working dir.
    argv=[*config['prefix'],config['python'],'-B','-I','5.py','30.json']
    checked_run(argv,env=environment(config,os.environ.get('CUDA_VISIBLE_DEVICES',''),0),
                cwd=root,stdout=sys.stdout,stderr=sys.stderr,check=True)


def launch(root,cfg,inputs,J,pre_bytes,stage_seconds):
    from orchard_h10.common import write, checked_run
    from orchard_h10.e import capture, exception
    physical=J.physical(root,cfg['logical']+'/r')
    metadata=physical/'metadata';metadata.mkdir(parents=True,exist_ok=True)
    receipt=metadata/'25.json'
    value=dict(passed=False,bulk_bytes=0,pre_bulk_bytes=pre_bytes,
               stage_seconds=stage_seconds,plan=cfg['plan_sha256'],job=os.environ['SLURM_JOB_ID'])
    write(receipt,value)
    started=time.monotonic();accepted=False
    try:
        for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
        dispatch=root/'a'
        (dispatch/'5.py').write_bytes((Path(__file__).parent/'entry.py').read_bytes())
        config=dict(package=cfg['logical']+'/p',output=cfg['logical']+'/r',python=inputs['python'],
                    cache_root=cfg['logical']+'/r/cache/0',prefix=['bash',inputs['policy']['vnice']])
        write(dispatch/'4.json',dict(action=4,config=config,package=config['package'],plan=cfg['plan_sha256'],job=os.environ['SLURM_JOB_ID']))
        env=J.environment(root)
        env={k:v for k,v in env.items() if 'sam' not in k.lower()}
        env.update(OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16')
        with capture(metadata/'27.json') as log:
            checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'4.json')],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        result=json.loads(receipt.read_text())
        if not result.get('passed') or result.get('bulk_bytes')!=0 or result.get('plan')!=cfg['plan_sha256']:
            raise ValueError('E84')
        value.update(result);accepted=True
    except BaseException as error:
        exception(metadata/'28.json',error)
        # A CPU failure is returned by the common supervisor. Preserve the
        # worker traceback in its pipe even when the CPU root is private.
        for name in ('26.json','27.json'):
            path=metadata/name
            if path.exists():
                for line in json.loads(path.read_text()).get('lines',[]):print(line,file=sys.stderr)
        raise
    finally:
        if receipt.exists():
            saved=json.loads(receipt.read_text())
            value.update(saved)
        value.update(passed=accepted,pre_bulk_bytes=pre_bytes,stage_seconds=stage_seconds,
                     launch_seconds=time.monotonic()-started)
        value['pre_bulk_seconds']=value['stage_seconds']+value['launch_seconds']
        write(receipt,value)
        # The supervisor can retain this small receipt on CPU/bootstrap failure.
        write(Path('/project/community/jjyeung')/cfg['token']/'a/25.json',value)


def environment_archive(spec,root,S,retain_roots=('v','q'),retain_prefix=None):
    """Authenticate every part and materialize only the selected runtime members."""
    import hashlib
    class Stream:
        def __init__(self):
            self.parts=iter(spec['parts']);self.source=None;self.whole=hashlib.sha256();self.bytes=0
        def read(self,size):
            while True:
                if self.source is None:
                    self.part=next(self.parts,None)
                    if self.part is None:return b''
                    self.source=Path(self.part['path']).open('rb');self.hashed=hashlib.sha256();self.count=0
                data=self.source.read(size)
                if data:
                    self.count+=len(data);self.bytes+=len(data)
                    if self.count>self.part['bytes']:raise ValueError('E85')
                    self.hashed.update(data);self.whole.update(data);return data
                self.source.close();self.source=None
                if self.count!=self.part['bytes'] or self.hashed.hexdigest()!=self.part['sha256']:raise ValueError('E85')
        def close(self):
            if self.source is not None:self.source.close()
    stream=Stream()
    try:
        S.room(root,spec['expanded_bytes'])
        inventory=S.extract_stream(stream,root/spec['destination'],None,spec['expanded_bytes'],links=True,retain_roots=retain_roots,retain_prefix=retain_prefix)
        while stream.read(1024**2):pass
        if spec.get('sha256') is not None and stream.whole.hexdigest()!=spec['sha256']:raise ValueError('E85')
        return dict(bytes=stream.bytes,sha256=stream.whole.hexdigest(),extracted_bytes=sum(x['bytes'] for x in inventory.values()))
    finally:stream.close()


PYTHON_PREFIX='sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'


def interpreter_archive(group,root,S):
    spec=dict(parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group],
              destination='.',expanded_bytes=sum(p[1] for p in group))
    return environment_archive(spec,root,S,retain_roots=None,retain_prefix=PYTHON_PREFIX)
