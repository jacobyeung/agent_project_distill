"""Boot pinned archives through job.stage and the production namespace."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import import_audit as A
DL=Path('/scratch/jjyeung/orch_n30/reads228/dl')

class Vpy(unittest.TestCase):
    def test_pinned_production_prebulk(self):
        raw=(HERE/'out/delivery.tgz').read_bytes();outer=A.unpack(raw);inner=A.unpack(outer['0.tgz'])
        base=Path(tempfile.mkdtemp(prefix='vpy_',dir=HERE.parent/'r1_fixtures_old'));p=base/'p';p.mkdir()
        for name,data in inner.items():
            dest=p/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        sys.path.insert(0,str(p))
        import l
        l.install(p)
        from orchard_h10 import job,boot
        from orchard_h10.common import template
        S,J,R,*_=template()
        cfg=A.decode(inner['9.json']);pub=A.decode(outer['0.json'])
        cfg.update({k:pub[k] for k in ('payload_bytes','payload_sha256','plan_sha256')})
        inputs=A.decode(outer['a/1.json']);assets=A.decode(inner['orchard_h10/vendor/ORCHARD_ASSETS.json'])
        root=base/'j';root.mkdir();os.environ.update(USER='jjyeung',SLURM_JOB_ID='173974')
        mapping={}
        for i,group in enumerate(assets['groups']):
            for n,(path,size,digest) in enumerate(group):mapping[path]=DL/('r%d_%d'%(i,n))
        for spec in inputs['archives']:
            for part in spec['parts']:
                path=DL/Path(part['path']).name
                if path.exists():mapping[part['path']]=path
        mapping[str(Path('/project/community/jjyeung')/cfg['token']/'0.tgz')]=base/'0.tgz'
        (base/'0.tgz').write_bytes(outer['0.tgz'])
        # The pinned Orchard bwrap binary is absent locally. Only its host
        # executable is substituted; J.namespace builds all production mounts.
        local_bwrap=Path('/usr/bin/bwrap')
        self.assertTrue(local_bwrap.is_file())
        asset_bwrap=assets['bwrap_pin']['path']
        original_copy=S.copy_parts;original_environment=boot.environment_archive;original_path=boot.Path
        evidence=dict(delivery_sha256=A.sha(raw),local_archives=str(DL),root=str(root),
                      bulk_bytes=0,archives=[],namespace='production argv plus a same-location bind for the scratch fixture')
        def copied(parts,dest,opener,**kwargs):
            if dest.name=='bwrap':
                data=local_bwrap.read_bytes();dest.write_bytes(data)
                return dict(bytes=len(data),sha256=A.sha(data))
            # Reuse only the authenticated immutable transport copy. Extraction
            # and all pre-bulk member selection still run through job.stage.
            cache=HERE/'tests/vpy_inguub3c/j/a/1'
            if dest.name=='1' and cache.exists() and base.is_relative_to(HERE):
                whole=hashlib.sha256()
                with cache.open('rb') as source:
                    for part in parts:
                        h=hashlib.sha256();left=part['bytes']
                        while left:
                            block=source.read(min(left,1024**2))
                            self.assertTrue(block);left-=len(block);h.update(block);whole.update(block)
                        self.assertEqual(h.hexdigest(),part['sha256'])
                    self.assertEqual(source.read(1),b'')
                os.link(cache,dest)
                return dict(bytes=cache.stat().st_size,sha256=whole.hexdigest())
            return original_copy(parts,dest,lambda part:mapping[part['path']].open('rb'),**kwargs)
        def mapped_path(value):return Path(mapping.get(str(value),value))
        inert=base/'0.sh';inert.write_text('#!/bin/sh\nexec sleep 30\n');inert.chmod(0o700)
        evidence['policy_fixture']='The authenticated vnice script is real; its terminator helper retains stdout/stderr for its real 30-second sleep interval, without signals or deletion.'
        original_namespace=J.namespace
        def namespace():
            for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
            return original_namespace(root)+['--bind',str(root),str(root),'--ro-bind',str(inert),inputs['policy']['terminator']]
        env=J.environment(root);env.update(OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
        def execute(script,config):
            argv=namespace()+[inputs['python'],'-B','-I',str(script),str(config)]
            result=subprocess.run(argv,env=env,cwd=root,capture_output=True,text=True)
            return dict(argv=argv,returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
        def environment(spec,r,s,**kwargs):
            if spec is inputs['archives'][3]:
                # Replay precisely the old input-2/input-4 member selection.
                old=original_environment(inputs['archives'][2],r,s)
                self.assertEqual(old['extracted_bytes'],0)
                d=J.physical(root,inputs['python'])
                self.assertFalse(d.exists());self.assertFalse(d.is_symlink())
                original_environment(inputs['archives'][4],r,s)
                evidence['old']=execute(root/'a/5.py',root/'a/4.json')
                self.assertNotEqual(evidence['old']['returncode'],0)
                self.assertIn('execvp '+inputs['python'],evidence['old']['stderr'])
                self.assertIn('No such file or directory',evidence['old']['stderr'])
                evidence['old']['selected_input_indexes']=[2,4]
            if spec is inputs['archives'][4]:return dict(bytes=sum(p['bytes'] for p in spec['parts']),extracted_bytes=3131)
            result=original_environment(spec,r,s,**kwargs)
            evidence['archives'].append(result)
            return result
        production_launch=boot.launch
        class BootComplete(Exception):pass
        def launch(r,c,i,j,pre_bytes,seconds):
            self.assertEqual(i,inputs)
            dispatch=root/'a'
            (dispatch/'5.py').write_bytes(inner['orchard_h10/entry.py'])
            config=dict(package=cfg['logical']+'/p',output=cfg['logical']+'/r',python=inputs['python'],
                        cache_root=cfg['logical']+'/r/cache/0',prefix=['bash',inputs['policy']['vnice']])
            (dispatch/'4.json').write_text(json.dumps(dict(action=4,config=config,package=config['package'],plan=cfg['plan_sha256'],job='173974')))
            shared=base/'shared'
            shared.mkdir()
            def launch_path(value):
                path=Path(value)
                return shared if str(path)=='/project/community/jjyeung' else original_path(mapping.get(str(value),value))
            with patch.object(J,'namespace',side_effect=lambda r:namespace()),patch.object(boot,'Path',side_effect=launch_path):
                production_launch(r,c,i,j,pre_bytes,seconds)
            evidence['fixed']=dict(returncode=0,production_capture=True)
            receipt=J.physical(root,cfg['logical']+'/r/metadata/25.json')
            evidence['boot']=A.decode(receipt.read_bytes());self.assertTrue(evidence['boot']['passed'])
            self.assertEqual(evidence['boot']['modules'],411)
            self.assertEqual(evidence['boot']['child_returncode'],0)
            self.assertEqual(evidence['boot']['worker_returncode'],0)
            self.assertIsNone(evidence['boot']['failed_module'])
            self.assertEqual(A.decode((shared/cfg['token']/'a/25.json').read_bytes()),evidence['boot'])
            self.assertEqual(evidence['boot']['bulk_bytes'],0)
            evidence.update(pre_bulk_bytes=pre_bytes,stage_seconds=seconds)
            # Resolve all staged links inside the namespace, including absolute
            # venv links. ldd checks the native ELF loader and linked libraries.
            audit=root/'a/6.py'
            audit.write_text('''import json,os,sys,subprocess
from pathlib import Path
roots=[Path('/scratch/jjyeung'),Path('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap')]
links=[];bad=[]
for root in roots:
 for path in root.rglob('*'):
  if path.is_symlink():
   links.append([str(path),os.readlink(path)])
   if not path.exists():bad.append(str(path))
exe=Path(sys.executable).resolve()
elf=subprocess.run(['/usr/bin/ldd',str(exe)],capture_output=True,text=True)
assert elf.returncode==0 and 'not found' not in elf.stdout,elf.stdout+elf.stderr
assert not bad,bad
print(json.dumps(dict(links=links,elf=str(exe),ldd=elf.stdout)))
''')
            result=execute(audit,dispatch/'4.json')
            self.assertEqual(result['returncode'],0,result['stderr'])
            evidence['path_audit']=json.loads(result['stdout'])
            # Only the selected runtime tree, package and policy may exist.
            d=J.physical(root,cfg['logical']+'/d')
            self.assertEqual(set(x.name for x in d.iterdir()),{'v','q'})
            self.assertEqual(set(x.name for x in (root/'sj').iterdir()),{'uv-python','b01ec87a6f29b','orch_n30'})
            self.assertFalse((root/'sj/orch_n30').is_file())
            evidence['passed']=True
            raise BootComplete()
        try:
            with patch.object(S,'copy_parts',side_effect=copied),patch.object(boot,'Path',side_effect=mapped_path),\
                 patch.object(boot,'environment_archive',side_effect=environment),patch.object(boot,'launch',side_effect=launch):
                with self.assertRaises(BootComplete):job.stage(root,cfg,inputs,S,J)
        finally:
            (HERE/'out/VPY_CHECKS.json').write_text(getattr(json,'_a0_dumps',json.dumps)(evidence,indent=2)+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
