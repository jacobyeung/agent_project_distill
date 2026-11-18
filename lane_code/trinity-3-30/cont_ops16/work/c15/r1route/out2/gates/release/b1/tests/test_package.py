"""CPU contract tests; small synthetic weights never stand in for a real parity run."""
import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

OUT=Path(__file__).resolve().parents[1]; ROOT=OUT.parent; SRC=OUT/'src'; PROD=SRC
sys.path[:0]=[str(SRC),str(SRC/'b'),str(OUT)]
from orchard_h10.common import canonical, sha, read_config, template
from orchard_h10.job import check_inputs, verify_config
from orchard_h10.export_pins import validate
from parity_kit import stage_restore
import fill_export


def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,sort_keys=True)+'\n')
def fresh():return Path(tempfile.mkdtemp(prefix='r2_',dir=OUT/'tests'))


def fixture_maker(export, artifact, items, **kwargs):
    return lambda item:dict(text='0',finish='stop')


class Package(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=read_config(OUT/'package')
        cls.old=read(OUT/'inputs_tower.json');cls.old.pop('export_pin',None)
        cls.pins=read(OUT/'export_544.json')

    def admitted(self,pins=None,inputs=None):
        package=fresh();(package/'a').mkdir()
        write(package/'a/export.json',pins or self.pins)
        inputs=copy.deepcopy(inputs or self.old)
        inputs['export_pin']=dict(path='a/export.json',**fill_export.pin((package/'a/export.json').read_bytes()))
        return inputs,package

    def test_544_and_camera_admission(self):
        inputs,package=self.admitted()
        verify_config(self.cfg)
        self.assertEqual(check_inputs(inputs,self.cfg,package=package),inputs)
        inputs['types']=['camera_displacement','camera_rotation','camera_movement_direction']
        check_inputs(inputs,self.cfg,package=package)
        inputs['types'].reverse()
        with self.assertRaisesRegex(ValueError,'type selection'):check_inputs(inputs,self.cfg,package=package)
        self.assertEqual(self.cfg['logical'],'/scratch/jjyeung/b01ec87a6f29b')
        self.assertNotEqual(self.cfg['token'],'b01ec87a6f29b')

    def test_each_export_hash_and_size_refuses_before_staging(self):
        for name in ('artifact','heads','full_weights'):
            for field in ('sha256','bytes'):
                for side in ('inputs','pins'):
                    with self.subTest(name=name,field=field,side=side):
                        pins=copy.deepcopy(self.pins);inputs=copy.deepcopy(self.old)
                        obj=inputs['files'][name] if side=='inputs' else pins[name]
                        obj[field]='0'*64 if field=='sha256' else obj[field]+1
                        inputs,package=self.admitted(pins,inputs)
                        with self.assertRaisesRegex(ValueError,'Export pin differs'):
                            check_inputs(inputs,self.cfg,package=package)

    def test_missing_modified_or_unsafe_pin_refuses(self):
        inputs,package=self.admitted()
        with self.assertRaises(KeyError):check_inputs(self.old,self.cfg,package=package)
        with self.assertRaises(FileNotFoundError):check_inputs(inputs,self.cfg,package=fresh())
        (package/'a/export.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'pin file differs'):check_inputs(inputs,self.cfg,package=package)
        for field,value in [('member_directory','../m544'),('step',True),('lineage','UNKNOWN')]:
            pins=copy.deepcopy(self.pins);pins[field]=value
            with self.assertRaises(ValueError):validate(pins)
        pins=copy.deepcopy(self.pins);pins['member_directory']='m100'
        inputs,package=self.admitted(pins)
        with self.assertRaisesRegex(ValueError,'member path'):check_inputs(inputs,self.cfg,package=package)

    def test_nonexport_pins_and_private_paths(self):
        inputs,package=self.admitted()
        self.assertEqual(inputs['archives'],self.old['archives'])
        self.assertEqual(inputs['policy'],self.old['policy'])
        self.assertEqual(inputs['files'],self.old['files'])
        S,J,*_=template()
        a=J.physical(Path('/tmp/a100'+self.cfg['token']),self.cfg['logical']+'/d')
        b=J.physical(Path('/tmp/a101'+self.cfg['token']),self.cfg['logical']+'/d')
        self.assertNotEqual(a,b)
        inputs['files']['sam_checkpoint']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Registered dependency'):
            check_inputs(inputs,self.cfg,package=package)

    def metadata_fixture(self,h11=False):
        root=fresh();pins=copy.deepcopy(self.pins)
        req=PROD/'b/work/n13/ret/native/paired/request.json'
        meta=PROD/'b/work/meta/x'
        prep=stage_restore.PREP
        paths=dict(config=meta/prep/'config.json',receipt=meta/prep/'prepared/s1_receipt.json',
                   data_receipt=meta/'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json')
        for name,p in paths.items():
            dest=root/pins['preparation'][name]['path'];dest.parent.mkdir(exist_ok=True)
            dest.write_bytes(p.read_bytes())
        receipt=read(paths['receipt']);cfg=read(paths['config'])
        artifact=dict(config_sha256=receipt['config_sha256'],base_identity=cfg['base_identity'],
                      frame_layout='duplicate',geometry_online=False)
        if h11:
            folder=Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/gates/lost/repin')/'in/h1_1_run_inputs'
            cfg=read(folder/'inputs/prepare_b000cf6bbd2346a59dc1d213e84ad066/config.json')
            data=read(folder/'inputs/data_receipt.json')
            # The real H1-1 receipt is absent. This explicit synthetic receipt tests
            # the known config-identity mismatch, not H1-1 receipt authentication.
            rec={**receipt,'config_sha256':read(folder/'binding.json')['config_sha256']}
            raw=json.dumps(rec).encode();data['preparation']['sha256']=hashlib.sha256(raw).hexdigest()
            cfg['preparation']=data['preparation']
            cfg_raw=json.dumps(cfg).encode();data['config']['sha256']=hashlib.sha256(cfg_raw).hexdigest()
            values=dict(config=cfg_raw,receipt=raw,data_receipt=json.dumps(data).encode())
            for name,raw in values.items():
                spec=pins['preparation'][name];spec.update(fill_export.pin(raw))
                spec['source_path']=(data['config']['path'] if name=='config' else
                                     data['preparation']['path'] if name=='receipt' else '/fixture/data_receipt.json')
                (root/spec['path']).write_bytes(raw)
        (root/'heads').mkdir();write(root/'heads/artifact.json',artifact)
        pins['artifact']=fill_export.pin((root/'heads/artifact.json').read_bytes())
        return root,pins,req

    def call_restore(self,root,pins,req):
        return stage_restore.stage(root/'weights',root/'heads',PROD/'b/work/meta/x',root/'restore',
                                   request=req,export_pins=pins,data_root=root)

    def test_real_544_prep_and_wrong_prep_pins(self):
        root,pins,req=self.metadata_fixture()
        with patch.object(stage_restore,'original_assets',side_effect=RuntimeError('metadata passed')):
            with self.assertRaisesRegex(RuntimeError,'metadata passed'):self.call_restore(root,pins,req)
            for name in ('config','receipt','data_receipt'):
                for field in ('sha256','bytes'):
                    bad=copy.deepcopy(pins);bad['preparation'][name][field]=('0'*64 if field=='sha256'
                                                          else bad['preparation'][name][field]+1)
                    with self.subTest(name=name,field=field):
                        with self.assertRaisesRegex(ValueError,'mismatch|size differs'):
                            self.call_restore(root,bad,req)

    def test_544_identity_with_h11_prep_refuses(self):
        root,pins,req=self.metadata_fixture(h11=True)
        with self.assertRaisesRegex(ValueError,'export architecture or identity differs'):
            self.call_restore(root,pins,req)

    def test_h11_supplied_data_config_checks(self):
        root=Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/gates/lost/repin')/'in/h1_1_run_inputs';data=read(root/'inputs/data_receipt.json')
        cfg_path=root/'inputs/prepare_b000cf6bbd2346a59dc1d213e84ad066/config.json';cfg=read(cfg_path)
        self.assertEqual(data['config']['sha256'],sha(cfg_path))
        self.assertEqual(data['preparation'],cfg['preparation'])
        self.assertEqual(data['preparation'],read(root/'binding.json')['preparation'])
        tree=ast.parse((PROD/'b/parity_kit/stage_restore.py').read_text())
        node=next(n for n in ast.walk(tree) if isinstance(n,ast.If)
                  and any(isinstance(s,ast.Raise) and isinstance(s.exc,ast.Call) and
                          s.exc.args and isinstance(s.exc.args[0],ast.Constant) and
                          s.exc.args[0].value=='data receipt binding differs' for s in n.body))
        code=compile(ast.Module(body=[node],type_ignores=[]),'production guard','exec')
        exec(code,dict(data=data,cfg=cfg,req=dict(config=data['config'])))
        self.assertEqual(cfg['frame_layout'],'duplicate')
        self.assertEqual(cfg['base_identity'],'c202236235762e1c871ad0ccb60c8ee5ba337b9a')
        self.assertNotEqual(data['config'],read(root/'inputs/request.json')['config'])

    def test_restore_structural_guards_are_unchanged(self):
        def guards(path):
            tree=ast.parse(path.read_text());result={}
            for node in ast.walk(tree):
                if not isinstance(node,ast.If):continue
                for stmt in node.body:
                    if (isinstance(stmt,ast.Raise) and isinstance(stmt.exc,ast.Call)
                            and stmt.exc.args and isinstance(stmt.exc.args[0],ast.Constant)):
                        result[stmt.exc.args[0].value]=ast.dump(node.test)
            return result
        old=guards(PROD/'b/parity_kit/stage_restore.py');new=guards(SRC/'b/parity_kit/stage_restore.py')
        for message,condition in old.items():self.assertEqual(new[message],condition,message)
        for name in ('original_assets','depth_shapes','prove_depth'):
            def function(path):
                node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
                return ast.dump(node)
            self.assertEqual(function(PROD/'b/parity_kit/stage_restore.py'),function(SRC/'b/parity_kit/stage_restore.py'))

    def test_worker_passes_the_authenticated_identity_path(self):
        from orchard_h10.runner import control,worker_args
        root=fresh();config=dict(package=str(SRC),output=str(root),export='e',binding='b',settings='s',
                                export_pin='6.json')
        control(config)
        argv=worker_args(dict(config=config,type=0,index=0,cards=1,stop_at=1,finish_by=2))
        self.assertEqual(argv[argv.index('--export-pin')+1],'6.json')
        self.assertEqual(argv[argv.index('--types')+1],'camera_displacement')

    def test_sealed_operator_loads_all_helpers(self):
        code=('import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);'
              'from orchard_h10.operator import load_helpers;'
              'cfg=load_helpers(Path(sys.argv[2]));'
              'from orchard_h10.export_pins import validate;'
              'assert cfg["logical"]=="/scratch/jjyeung/b01ec87a6f29b";'
              'print(cfg["plan_sha256"])')
        result=subprocess.run([sys.executable,'-B','-I','-c',code,str(SRC),str(OUT/'package')],
                              check=True,capture_output=True,text=True)
        self.assertEqual(result.stdout.strip(),self.cfg['plan_sha256'])

    def test_lineage_step_reach_journal_and_curve(self):
        from h1eval.h10 import launch
        from h1eval.cli import write_curve
        from h1eval.items import load_manifest
        for lineage,step in [('SFT',544),('SFT',100),('RL',37)]:
            root=fresh();(root/'export').mkdir();(root/'export/weight').write_bytes(b'fixture')
            write(root/'binding.json',{});write(root/'pins.json',{**self.pins,'lineage':lineage,'step':step})
            args=launch.parser().parse_args(['--items',str(SRC/'items/devs1_routed.json'),
                '--export',str(root/'export'),'--artifact-manifest',str(root/'binding.json'),
                '--reader-root',str(SRC/'b'),'--out',str(root/'journal'),
                '--export-pin',str(root/'pins.json'),'--reader-entry','fixture:make',
                '--shard','0/1000','--arms','own','--modes','none','--device','cpu'])
            with patch('sys.stdout',new=io.StringIO()):launch.run(args,make_real=fixture_maker)
            binding=read(root/'journal/environment.json')['binding']
            self.assertEqual((binding['lineage'],binding['step']),(lineage,step))
            self.assertTrue(launch.read_records(root/'journal/items.jsonl'))
            curve=write_curve(root,[],load_manifest(SRC/'items/devs1_routed.json'),root/'export',
                              binding,32,['own'],[])
            self.assertEqual((curve['lineage'],curve['step']),(lineage,step))
            self.assertEqual(curve['bootstrap'],dict(draws=10000,seed=20261115,unit='room',interval=.95))

    def test_identity_and_byte_inventory(self):
        from h1eval.cli import code_hash
        from h1eval.h10.parity_adapter import reader_code_hash
        old=read(OUT/'AUDIT_R1.json')
        self.assertEqual(sha(Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/gates/lost/repin')/'in/prod_pkg/0.tgz'),old['archive'])
        self.assertEqual(canonical(read(PROD/'9.json')),old['plan'])
        self.assertEqual(sha(Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/gates/lost/repin')/'in/prod_pkg/a/1.json'),old['raw_inputs'])
        self.assertNotEqual(code_hash(SRC/'b/e2e_reader'),old['reader'])
        self.assertEqual(read(SRC/'items/devs1_routed.json')['item_set_sha256'],old['item_set'])
        self.assertEqual(reader_code_hash(PROD/'b'),old['parity'])
        self.assertNotEqual(reader_code_hash(SRC/'b'),old['parity'])
        self.assertNotEqual(code_hash(),old['evaluator'])
        allowed={'b/e2e_reader/perception_memo.py','8.py','9.json','orchard_h10/job.py','orchard_h10/operator.py',
                 'orchard_h10/build.py','orchard_h10/prepare.py','orchard_h10/runner.py',
                 'orchard_h10/export_pins.py','h1eval/h10/launch.py','h1eval/h10/parity_adapter.py','b/parity_kit/stage_restore.py','b/e2e_reader/servers.py', 'h1eval/perception.py', 'h1eval/h10/perception_own.py', 'b/e2e_reader/stage1.py', 'h1eval/h10/depth_snapshot.py', 'b/e2e_reader/grounding.py','b/e2e_reader/real.py','b/e2e_reader/parity.py'}
        def inventory(path):
            with tarfile.open(path) as tar:return {m.name:tar.extractfile(m).read() for m in tar if m.isfile()}
        a=inventory(Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/gates/lost/repin')/'in/prod_pkg/0.tgz');b=inventory(OUT/'package/0.tgz')
        changed={n for n in a.keys()|b.keys() if a.get(n)!=b.get(n)}
        self.assertEqual(changed,allowed)
        for name,pin in self.cfg['payload_pins'].items():
            self.assertEqual(fill_export.pin(b[name]),pin)


class StreamingHelper(unittest.TestCase):
    def fixture(self):
        root=fresh();files={'m-any/heads.pt':b'heads','m-any/full_weights/w':b'weight',
                          'm-any/full_weights/i':b'index'}
        full=dict(schema='full-ft-export-v1',dtype='bfloat16',files=[dict(name='w',**fill_export.pin(b'weight'))],
                  index=dict(name='i',**fill_export.pin(b'index')))
        files['m-any/full_weights/full_weights.json']=json.dumps(full).encode()
        artifact=dict(heads=fill_export.pin(b'heads'),full_weights=fill_export.pin(files['m-any/full_weights/full_weights.json']),
                      config_sha256='84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb',
                      base_identity='c202236235762e1c871ad0ccb60c8ee5ba337b9a',frame_layout='duplicate',geometry_online=False)
        files['m-any/artifact.json']=json.dumps(artifact).encode()
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w') as tar:
            for name,raw in files.items():
                entry=tarfile.TarInfo(name);entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
        raw=stream.getvalue();parts=[]
        for i in range(4):
            path=root/str(i);path.write_bytes(raw[i*len(raw)//4:(i+1)*len(raw)//4]);parts.append(path)
        done=root/'done';done.write_text('q8/test.tar '+str(len(raw))+' '+hashlib.sha256(raw).hexdigest()+'\n')
        return parts,done

    def test_four_parts_and_wrong_done(self):
        parts,done=self.fixture();value,artifact,archive=fill_export.scan(parts,done,'q8/test.tar')
        self.assertEqual(value['member_directory'],'m-any');self.assertEqual(len(archive['parts']),4)
        self.assertEqual(value['heads'],fill_export.pin(b'heads'))
        original=done.read_text()
        for field,bad in [(0,'q8/other.tar'),(1,'1'),(2,'0'*64)]:
            words=original.split();words[field]=bad;done.write_text(' '.join(words)+'\n')
            with self.assertRaisesRegex(ValueError,'done'):fill_export.scan(parts,done,'q8/test.tar')
        done.write_text(original)
        with self.assertRaises((ValueError,tarfile.TarError)):
            fill_export.scan(list(reversed(parts)),done,'q8/test.tar')

    def test_helper_writes_pins_inputs_and_small_prep_archive(self):
        parts,done=self.fixture();root=done.parent
        base=PROD/'b/work/meta/x/fsw/ap/8865619b/runs/469ddece/inputs'
        prep=base/'prepare_dd26bb95f37a43789206c6e4d4cd94bd'
        argv=['fill_export.py','--parts',*map(str,parts),'--done',str(done),'--object','q8/test.tar',
              '--config',str(prep/'config.json'),'--receipt',str(prep/'prepared/s1_receipt.json'),
              '--data-receipt',str(base/'data_receipt.json'),'--lineage','SFT','--step','100',
              '--out',str(root/'export.json'),'--prep-tar',str(root/'prep.tar'),
              '--base-inputs',str(Path('/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out2/gates/lost/repin')/'in/prod_pkg/a/1.json'),'--inputs-out',str(root/'inputs.json')]
        with patch.object(sys,'argv',argv):fill_export.main()
        pins=validate(read(root/'export.json'));inputs=read(root/'inputs.json')
        self.assertEqual(pins['step'],100);self.assertEqual(pins['member_directory'],'m-any')
        self.assertEqual(inputs['export_pin']['sha256'],sha(root/'export.json'))
        self.assertEqual(inputs['files']['heads']['bytes'],5)
        self.assertEqual(inputs['types'],['camera_displacement','camera_rotation','camera_movement_direction'])
        with tarfile.open(root/'prep.tar') as tar:
            for name in ('config','receipt','data_receipt'):
                raw=tar.extractfile(pins['preparation'][name]['path']).read()
                self.assertEqual(fill_export.pin(raw),{k:pins['preparation'][name][k] for k in ('sha256','bytes')})


if __name__=='__main__':unittest.main(verbosity=2)
