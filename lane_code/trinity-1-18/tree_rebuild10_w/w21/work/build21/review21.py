from pathlib import Path
import sys,json,base64,unittest,os,tarfile,io
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from naming21 import scan_decoded,neutral_map
from jobtest import Job20
class Review21(unittest.TestCase):
    def test_log_names(self):
        from launch_r2.build import WORDS,bad_string
        hashes=J.load(B/'kits/q/b/wh.json')
        for word in WORDS:
            line='event "'+word+'": /a/'+word+'/file 400\n'
            safe=J.screen(line,WORDS,hashes)
            self.assertFalse(bad_string(safe,hashes));self.assertIn('400',safe)
        self.assertEqual(J.screen('ok 400\n',WORDS,hashes),'ok 400\n')
    def test_bootstrap_map_checks(self):
        from copy import deepcopy
        from jobtest import reseal,rawcap
        Job20.setUpClass();spec=deepcopy(Job20.spec)
        pool=Job20.pool/spec['p_root'];pool.mkdir(parents=True,exist_ok=True)
        a=pool/'ANON_OK.json';a.write_text('{}')
        original=pool/'k/0.json';original.parent.mkdir(exist_ok=True);original.write_text('{}')
        spec.update(p_files={'ANON_OK.json':J.sha(a),'k/0.json':J.sha(original)},local_map='k/l.json',link_checks=[dict(path=str(a),sha256=J.sha(a))])
        from launch_r2.build import capsule_json
        (Job20.kit/'k/l.json').write_bytes(capsule_json(dict(value='opaque')))
        (Job20.kit/'k/p.json').write_bytes(capsule_json(spec));reseal(Job20.kit)
        J.write(Job20.root/'empty.json',{})
        with patch.object(J,'stage_payload',return_value={}),patch.object(J.subprocess,'run',return_value=type('Result',(),dict(returncode=0))()):
            self.assertEqual(J.bootstrap(Job20.kit,Job20.root/'empty.json',Job20.root/'bootstrap'),0)
            self.assertEqual(J.load(Job20.root/'bootstrap/h/k/0.json'),dict(value='opaque'))
            spec['link_checks'][0]['sha256']='0'*64
            (Job20.kit/'k/p.json').write_bytes(capsule_json(spec));reseal(Job20.kit)
            with self.assertRaisesRegex(ValueError,'E10'):J.bootstrap(Job20.kit,Job20.root/'empty.json',Job20.root/'bad_link')
            spec['p_files'].pop('ANON_OK.json');(Job20.kit/'k/p.json').write_bytes(capsule_json(spec));reseal(Job20.kit)
            with self.assertRaisesRegex(ValueError,'E44'):J.bootstrap(Job20.kit,Job20.root/'empty.json',Job20.root/'no_anon')
    def test_anon_inventory(self):
        spec=J.load(B/'kits/q/k/p.json')
        self.assertEqual(spec['p_files']['ANON_OK.json'],J.sha(L.parent/'ext/pwrap/ANON_OK.json'))
    def test_decoded_scan(self):
        value=scan_decoded(B/'kits/q')
        J.write(B/'proofs/operator/SCAN.json',value)
    def test_env_aliases(self):
        from student_pilot.orchard_paths import enabled
        with patch.dict(os.environ,{'Q_E1':'1'},clear=True):self.assertTrue(enabled())
        with patch.dict(os.environ,{'STUDENT_ORCHARD':'1'},clear=True):self.assertTrue(enabled())
        with patch.dict(os.environ,{'Q_E1':'0','STUDENT_ORCHARD':'1'},clear=True):self.assertFalse(enabled())
        from student_pilot.job_env import key,ALIASES
        with patch.dict(os.environ,{},clear=True):
            for old in ALIASES:self.assertEqual(key(old),old)
            self.assertEqual(key('OTHER'),'OTHER')
        with patch.dict(os.environ,{v:'opaque' for v in ALIASES.values()},clear=True):
            for old,new in ALIASES.items():self.assertEqual(key(old),new)
    def test_opaque_model_and_frame_paths(self):
        from student_pilot import orchard_paths,students,r2_frames,grounding_train,orchard_admission
        root=B/'proofs/review/opaque';root.mkdir(parents=True,exist_ok=True)
        frames=root/'data2root';frames.mkdir(exist_ok=True);(frames/'f.png').write_bytes(b'fixture')
        env=dict(Q_E1='1',Q_E3=str(root/'m'),Q_E4=json.dumps({'/data2':str(frames)}),Q_E5='m8a9e'.encode().hex())
        with patch.dict(os.environ,env,clear=True),patch.object(orchard_paths,'PROJECT',root):
            self.assertEqual(students.runtime_student(),'m8a9e')
            self.assertEqual(students.get_student('m8a9e')['snapshot'].parent.parent.name,'a32330d0')
            self.assertEqual(orchard_paths.resolve_read('/data2/f.png'),frames/'f.png')
            self.assertEqual(r2_frames.resolve_frame('/data2/f.png'),frames/'f.png')
            grounding_train.bind_frames({'frame_root':str(frames)})
            self.assertEqual(json.loads(os.environ['Q_E4']),{'/data2':str(frames)})
            self.assertNotIn('STUDENT_FRAME_ROOT_MAP',os.environ)
            with patch.dict(os.environ,{'Q_E2':'unknown'}),patch.object(orchard_admission,'command',side_effect=AssertionError('No scheduler call')):
                with self.assertRaisesRegex(ValueError,'Unknown Slurm site'):orchard_admission.allocation()
    def test_map_and_link_checks(self):
        source=J.load(L.parent/'ext/pwrap/k/0.json');v,checks=neutral_map(source)
        self.assertEqual(len(checks),2)
        self.assertEqual(checks[1]['sha256'],source['model']['sha256'])
        self.assertNotIn('distill',json.dumps(v));self.assertNotIn('qwen',json.dumps(v).lower())
    def test_snapshot(self):
        root=B/'proofs/review';root.mkdir(parents=True,exist_ok=True)
        def make(name,members):
            p=root/(name+'.tar')
            with tarfile.open(p,'w') as a:
                for n,raw in members:
                    m=tarfile.TarInfo(n);m.size=len(raw);a.addfile(m,io.BytesIO(raw))
            return p
        p=make('input',[('cache/snapshots/r/config.json',b'{}')]);J.snapshot(p,J.sha(p),root/'good','r')
        self.assertEqual((root/'good/config.json').read_bytes(),b'{}')
        with self.assertRaises(ValueError):J.snapshot(p,'0'*64,root/'bad','r')
        with self.assertRaises(ValueError):J.snapshot(p,J.sha(p),root/'absent','s')
        p=make('escape',[('cache/snapshots/r/../bad',b'{}')])
        with self.assertRaises(ValueError):J.snapshot(p,J.sha(p),root/'escape','r')
        p=make('duplicate',[('cache/snapshots/r/config.json',b'{}')]*2)
        with self.assertRaises(ValueError):J.snapshot(p,J.sha(p),root/'duplicate','r')
        p=root/'link.tar'
        with tarfile.open(p,'w') as a:
            item=tarfile.TarInfo('link');item.type=tarfile.SYMTYPE;item.linkname='/outside';a.addfile(item)
        with self.assertRaisesRegex(ValueError,'E45'):J.snapshot(p,J.sha(p),root/'link','r')
