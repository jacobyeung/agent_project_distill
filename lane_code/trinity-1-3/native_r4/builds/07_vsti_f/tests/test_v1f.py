"""Return and packet regressions; remote transports are replaced at their boundaries."""
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import errno,io,sys,tarfile,unittest,uuid
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
        self.patches=[patch.object(self.module,'identity',return_value=self.root/'pool'),
                      patch.object(self.module,'pool_operation',return_value=dict(verified=True)),
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
        with (self.run/'excess.json').open('wb') as f:f.seek(512*1024**2);f.write(b' ')
        try:raise RuntimeError('prepare phase failed')
        except RuntimeError as e:phase=o.exception_record(e)
        data=self.assert_minimal(self.finish(phase),True)
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
        with p.open('wb') as f:f.seek(512*1024**2);f.write(b' ')
        result=self.finish();data=self.read_archive(result)
        self.assertTrue(result['complete']);self.assertNotIn('cell/g/scaled/huge.npz',data)
        self.assertIn('j0/items.jsonl',data);self.assertIn('j0/CANARY.json',data)

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
