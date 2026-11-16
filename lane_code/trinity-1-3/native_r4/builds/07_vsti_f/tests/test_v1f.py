"""Return and packet regressions; remote transports are replaced at their boundaries."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import errno,io,os,sys,tarfile,unittest,uuid
B=Path(__file__).resolve().parents[1];sys.path.append(str(B/'code'))
from adapter import dump,load,sha
import o

class Returns(unittest.TestCase):
    def setUp(self):
        self.root=B/'work'/('f_'+uuid.uuid4().hex);self.root.mkdir()
        self.run=self.root/'run';self.run.mkdir()
        self.config=dict(token='123456789abcdef012345678',binding='a'*64)
        self.module=o.imports()[2]
        dump(self.run/'PHASES.json',[dict(name='stage')])
        dump(self.run/'RESULT.json',dict(missing=[]))
        dump(self.run/'p/PROOF.json',dict(proven=False))
        dump(self.run/'j0/COMPLETE.json',dict(keys=[]))
        dump(self.run/'j0/CANARY.json',dict(pass_=True))
        (self.run/'j0/items.jsonl').write_text('{"key":"q1"}\n')
        dump(self.root/'STAGING.json',dict(passed=True))
        (self.root/'b.log').write_bytes(b'x'*(2*1024**2+11)+b'tail')
        (self.root/'a.log').write_text('stage log')
        self.patches=[patch.object(self.module,'pool_operation',return_value=dict(verified=True)),
                      patch.object(self.module,'upload',return_value=dict(verified=True))]
        self.mocks=[p.start() for p in self.patches]
        for p in self.patches:self.addCleanup(p.stop)
    def finish(self,phase=None):
        return o.finish_return(self.module,self.root,self.run,self.config,1 if phase else 0,
                               phase['error'] if phase else None,phase)
    def read_archive(self,result):
        with tarfile.open(Path(result['local_return'])/'result.tar.gz') as t:
            return {m.name:t.extractfile(m).read() for m in t if m.isfile()}
    def assert_minimal(self,result,phase=False):
        import json
        self.assertTrue(result['returned']);self.assertFalse(result['complete'])
        data=self.read_archive(result);f=json.loads(data['FAILURE.json'])
        self.assertIn('Traceback',f['return_error']['traceback'])
        if phase:self.assertIn('Traceback',f['phase_error']['traceback'])
        for name in ('PHASES.json','STAGING.json','INVENTORY.json','a.log','b.log','p/PROOF.json',
                     'j0/items.jsonl','j0/COMPLETE.json','j0/CANARY.json','RESULT.json','COMPLETE.json'):
            self.assertIn(name,data)
        self.assertEqual(len(data['b.log']),2*1024**2);self.assertTrue(data['b.log'].endswith(b'tail'))
        self.assertEqual(result['token'],self.config['token']);self.assertEqual(result['plan_sha256'],self.config['binding'])
        return data
    def test_phase_and_expanded_cap(self):
        (self.run/'excess.json').write_text('excess')
        try:raise RuntimeError('prepare phase failed')
        except RuntimeError as e:phase=o.exception_record(e)
        original=Path.stat
        def size(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path.name=='excess.json':
                fields=list(value);fields[6]=512*1024**2+1;return os.stat_result(fields)
            return value
        with patch.object(Path,'stat',size):data=self.assert_minimal(self.finish(phase),True)
        import json
        inv=json.loads(data['INVENTORY.json'])
        self.assertIn('excess.json',inv['excluded'])
        self.assertIn('expanded return exceeds cap',json.loads(data['FAILURE.json'])['return_error']['traceback'])
    def test_full_publish_exception(self):
        original=self.module.publish;calls=[]
        def publish(*args,**kwargs):
            calls.append((args,kwargs))
            if len(calls)==1:raise RuntimeError('injected full publication error')
            return original(*args,**kwargs)
        with patch.object(self.module,'publish',side_effect=publish):result=self.finish()
        self.assert_minimal(result)
        self.assertEqual(len(calls),2);self.assertEqual(calls[0][0][1:4],calls[1][0][1:4])
        self.assertEqual(calls[0][1],calls[1][1])
    def test_success_preserves_full_return(self):
        p=self.run/'cell/g/scaled/a.npz';p.parent.mkdir(parents=True);p.write_bytes(b'prepared array')
        raw=self.run/'cell/g/raw/a.npz';raw.parent.mkdir();raw.write_bytes(b'raw array')
        expected={str(p.relative_to(self.run)):p.read_bytes() for p in self.run.rglob('*') if p.is_file() and not o.omitted_prepare(p.relative_to(self.run))}
        result=self.finish();self.assertTrue(result['complete']);data=self.read_archive(result)
        for name,blob in expected.items():self.assertEqual(data[name],blob)
        self.assertNotIn('cell/g/raw/a.npz',data);self.assertNotIn('FAILURE.json',data)
        self.assertEqual(data['b.log'],(self.root/'b.log').read_bytes())
    def test_copy_failure_falls_back(self):
        original=o.attach
        def attach(source,target):
            if 'return' in target.parts:raise OSError(errno.ENOSPC,'injected full copy failure')
            return original(source,target)
        with patch.object(o,'attach',side_effect=attach):result=self.finish()
        self.assert_minimal(result)
    def test_suffix_failure_falls_back(self):
        (self.run/'unexpected.bin').write_bytes(b'unknown')
        self.assert_minimal(self.finish())
    def test_unverified_publication_falls_back(self):
        original=self.module.publish;calls=[]
        def publish(*args,**kwargs):
            calls.append(args)
            return dict(returned=False) if len(calls)==1 else original(*args,**kwargs)
        with patch.object(self.module,'publish',side_effect=publish):self.assert_minimal(self.finish())
    def test_storage_fallback(self):
        original=o.build_return
        def build(root,runroot,dest,*args,**kwargs):
            if dest.parent==self.root:raise OSError(errno.ENOSPC,'injected job disk full')
            return original(root,runroot,dest,*args,**kwargs)
        emergency=self.root/'independent';emergency.mkdir()
        with patch.object(o,'build_return',side_effect=build),patch.object(o.tempfile,'mkdtemp',return_value=str(emergency)) as alloc:
            self.assert_minimal(self.finish())
        self.assertEqual(alloc.call_args.kwargs['dir'],'/dev/shm')
    def test_geometry_cap_trim_preserves_protected(self):
        p=self.run/'cell/g/scaled/huge.npz';p.parent.mkdir(parents=True)
        p.write_bytes(b'geometry')
        original=Path.stat
        def size(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path.name=='huge.npz':
                fields=list(value);fields[6]=512*1024**2+1;return os.stat_result(fields)
            return value
        with patch.object(Path,'stat',size):result=self.finish()
        data=self.read_archive(result)
        self.assertTrue(result['complete']);self.assertNotIn('cell/g/scaled/huge.npz',data)
        self.assertIn('j0/items.jsonl',data);self.assertIn('j0/CANARY.json',data)

    def test_digit_token_real_identity_and_pool_worker(self):
        for head in '0123456789abcdef':
            token=head+'123456789abcdef01234567'
            self.assertEqual(self.module.identity(self.module.AUTHORIZED_POOL,token),self.module.AUTHORIZED_POOL)
        with self.assertRaises(ValueError):self.module.identity(self.module.AUTHORIZED_POOL,'../unsafe')
        result=self.finish();pool=self.root/'real_pool'
        receipt=self.module.pool_worker('publish',pool,self.config['token'],4*1024**2,local=result['local_return'])
        self.assertTrue(receipt['verified'])
        self.assertEqual(sha(pool/self.config['token']/'result.tar.gz'),sha(Path(result['local_return'])/'result.tar.gz'))

    def test_compressed_cap_trims_only_geometry(self):
        p=self.run/'cell/g/scaled/random.npz';p.parent.mkdir(parents=True)
        p.write_bytes(os.urandom(200000))
        with patch.object(self.module,'mode_limit',return_value=100000):result=self.finish()
        data=self.read_archive(result);self.assertTrue(result['complete'])
        self.assertNotIn('cell/g/scaled/random.npz',data)
        for name in ('p/PROOF.json','j0/CANARY.json','j0/items.jsonl','RESULT.json'):
            self.assertEqual(data[name],(self.run/name).read_bytes())
    def test_proof_phase_traceback(self):
        with patch.object(o.subprocess,'run',side_effect=RuntimeError('proof worker failed')):
            self.assertEqual(o.run_phase([], '/x/p.py', self.run, {}, io.StringIO(), 1),0)
        failure=load(self.run/'FAILURE.json')
        self.assertIn('Traceback',failure['phase_error']['traceback'])
        data=self.read_archive(self.finish());self.assertIn(b'proof worker failed',data['FAILURE.json'])
    def test_run_phase_and_return_failure(self):
        modules=o.imports();token=self.config['token'];tmp=self.root/'tmp';tmp.mkdir()
        config=deepcopy(self.config);archive=self.root/'code.tar';archive.write_bytes(b'fixture')
        config.update(added={k:dict(path=o.PREFIX+k+'.tar',name=o.CLOUD+k+'.tar',sha256='a'*64,
                                   bytes=7,generation='1',verified=True) for k in 'abcd'},
                      family=dict(parent_config={},inputs=dict(keys=[])))
        config['added']['c']['path']=str(archive)
        config['binding']=o.digest({k:v for k,v in config.items() if k!='binding'})
        dump(self.root/'config.json',config)
        jobroot=tmp/('a15_123_'+token)
        def path(value):return tmp if str(value)=='/tmp' else Path(value)
        def phase(*args,**kwargs):
            (jobroot/'run/bad.bin').write_bytes(b'unexpected output')
            raise RuntimeError('injected allocation phase failure')
        with patch.object(o,'Path',side_effect=path),patch.object(o,'validate_additions'),patch.object(o,'extract'),patch.object(o,'sha',return_value='a'*64),patch.object(o,'imports',return_value=modules),patch.object(modules[3],'card',side_effect=phase),patch.dict(os.environ,SLURM_JOB_ID='123',SLURM_JOB_PARTITION='general'):
            result=o.run(self.root/'config.json')
        data=self.read_archive(result)
        import json
        failure=json.loads(data['FAILURE.json'])
        self.assertIn('injected allocation phase failure',failure['phase_error']['traceback'])
        self.assertIn('unexpected return member',failure['return_error']['traceback'])
        self.assertTrue(result['returned'])

class Packet(unittest.TestCase):
    def test_all_four_archives_reject_links(self):
        root=B/'work'/('packet_f_'+uuid.uuid4().hex);root.mkdir()
        for key in 'abcd':
            for kind in (tarfile.LNKTYPE,tarfile.SYMTYPE):
                case=root/(key+kind.decode());case.mkdir()
                records={};family={'added':{},'limits':{'full':{}}}
                for asset in 'abcd':
                    p=case/(asset+'.tar')
                    with tarfile.open(p,'w') as t:
                        d=tarfile.TarInfo('folder');d.type=tarfile.DIRTYPE;t.addfile(d)
                        f=tarfile.TarInfo('folder/file');f.size=2;t.addfile(f,io.BytesIO(b'ok'))
                        if asset==key:
                            link=tarfile.TarInfo('link');link.type=kind;link.linkname='folder/file';t.addfile(link)
                    records[asset]=dict(path=str(p),name=o.CLOUD+asset+'.tar',sha256=sha(p),bytes=p.stat().st_size,generation='1',verified=True)
                    family['added'][asset]=dict(sha256=sha(p))
                dump(case/'family.json',family);dump(case/'receipts.json',records)
                with patch.object(o,'PREFIX',str(case)+'/'):
                    with self.assertRaisesRegex(ValueError,'non-file/non-directory'):
                        o.packet(case/'family.json',case/'receipts.json',case/'packet','123456789abcdef012345678')
                self.assertFalse((case/'packet').exists())
    def test_regular_and_directory_accepted(self):
        root=B/'work'/('packet_ok_'+uuid.uuid4().hex);root.mkdir();p=root/'input.tar'
        with tarfile.open(p,'w') as t:
            m=tarfile.TarInfo('directory');m.type=tarfile.DIRTYPE;t.addfile(m)
            m=tarfile.TarInfo('directory/file');m.size=1;t.addfile(m,io.BytesIO(b'x'))
        o.check_packet_tar(p)
if __name__=='__main__':unittest.main()
