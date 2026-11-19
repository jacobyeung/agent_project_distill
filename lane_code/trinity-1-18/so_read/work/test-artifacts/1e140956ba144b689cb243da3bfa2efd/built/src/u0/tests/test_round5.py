"""Round-5 packaging and operation contracts, with fail-before controls."""
import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
import uuid
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
INPUT=Path(os.environ['READ_INPUT_SRC'])
BEFORE=os.environ.get('READ_ROUND5_BEFORE')=='1'
E=L/'work/round5-before-u0' if BEFORE else SRC/'u0'
OUT=L/'out_round5' if BEFORE else L/'out'
OP=Path(os.environ.get('READ_OPERATOR4_SOURCE',str(L/'work/operator4')))
sys.path[:0]=[str(SRC),str(SRC/'b'),str(INPUT/'tree')]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def write(path,value):path.write_text(json.dumps(value,sort_keys=True))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def fresh():
    root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True);return root

class ReachedCopy(ValueError):pass

class Round5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=fresh();cls.base=cls.root/'base';cls.base.mkdir()
        cls.builder=load('builder5',E/'a19.py')
        for rel in ('package/0.tgz','package/0.json','package/BATCH.sh','package/3.py',
                    'package/a/0.json','package/a/4.py','package/a/7.py','fetch_return.py',
                    'tower_sequence.py','unpack_return.py','package/a/5.py'):
            source=(OP/rel if rel in ('tower_sequence.py','unpack_return.py','package/a/5.py') else INPUT.parent/rel)
            target=cls.base/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        cfg=json.loads(cls.builder.unpack((cls.base/'package/0.tgz').read_bytes())['9.json'])
        cls.binding=dict(cfg['export_binding'],step=600,member_directory='m600',
            object='q8/8865619b/673bc60f_m600.tar',archive_bytes=4,archive_sha256='2'*64,
            done='/project/community/jjyeung/okh7/abcdef/5',
            prep_paths={k:'/project/community/jjyeung/okh7/abcdef/'+str(i) for i,k in enumerate(('config','receipt','data_receipt'),7)})
        write(cls.root/'binding.json',cls.binding)
        cls.options={} if BEFORE else dict(manifest_path=L/'out/patches/MANIFEST.json',extension_pins_path=L/'out/kit_parity50/EXTENSION_PINS.json')
        cls.target=cls.root/'built'
        cls.builder.build(cls.base,SRC,cls.root/'binding.json',cls.target,'ab0123456789',enable_extensions=True,**cls.options)

    def helpers(self):
        self.assertTrue((E/'a20.py').is_file(),'Missing executable binding/operation/gate helper')
        return load('operations5',E/'a20.py')

    def test_f1_batch_wrapper_and_real_bundle_guard(self):
        batch=(self.target/'package/BATCH.sh').read_text()
        self.assertIn('#SBATCH --exclude=orchard-community-2\n',batch)
        self.assertIn('trap fin EXIT',batch);self.assertIn("trap 'kill -USR1 $PID 2>/dev/null' USR1",batch)
        self.assertIn('tail -n 60 "$L"',batch);self.assertIn('R=$P/a/x${SLURM_JOB_ID:-0}',batch)
        subprocess.run(['bash','-n',str(self.target/'package/BATCH.sh')],check=True)
        # The vendored wrapper must equal cont_ops' function, byte for byte.
        reference=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops17/work/build_r10.py')
        nodes=ast.parse(reference.read_text()).body
        selected=[n for n in nodes if isinstance(n,ast.FunctionDef) and n.name=='wrap_batch' or
                  isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HEAD_OLD' for t in n.targets)]
        scope={};exec(compile(ast.Module(body=selected,type_ignores=[]),str(reference),'exec'),scope)
        raw=self.builder.bootstrap(batch)
        plain=self.builder.batch(self.builder.tarbytes(raw),'ab0123456789').encode()
        self.assertEqual(batch.encode(),scope['wrap_batch'](plain,'ab0123456789'))
        node=load('node5',self.target/'package/a/5.py');root=fresh()
        vendor=INPUT/'orchard_h10/vendor/return_io.py'
        def write_test(pool,token):
            dest=Path(pool)/token/'.wtest';dest.parent.mkdir(parents=True)
            shared=Path(os.environ['READ_TEST_TMP'])/'write-test-4MiB'
            if not shared.exists():shared.write_bytes(bytes(4*1024**2))
            os.link(shared,dest)
            (root/'6.py').write_bytes(vendor.read_bytes())
            return dict(bytes=dest.stat().st_size,sha256=sha(dest))
        from orchard_h10 import common
        results=types.SimpleNamespace(write_test=write_test,__file__=str(vendor.with_name('orchard_results.py')))
        with patch.object(common,'template',return_value=(None,None,results,None,None)):
            proof=node.check_bundle_guard(self.target/'package',root)
        self.assertIs(proof['passed'],True);self.assertEqual(proof['operator_sha256'],sha(self.target/'tower_sequence.py'))

    def test_f2_pins_refuse_before_copy(self):
        manifest=json.loads((L/'out/patches/MANIFEST.json').read_text())
        original={r:(self.base/r).read_bytes() for r in ('package/0.tgz','package/0.json','package/BATCH.sh','tower_sequence.py','unpack_return.py','package/a/5.py')}
        def attempt(options=None,source=SRC):
            opts=self.options if options is None else options
            with patch.object(self.builder,'tarbytes',side_effect=ReachedCopy('Unpinned input reached copy/build')):
                self.builder.build(self.base,source,self.root/'binding.json',self.root/'refused','ab0123456789',enable_extensions=True,**opts)
        for rel in ('tower_sequence.py','unpack_return.py','package/a/5.py'):
            with self.subTest(operator=rel):
                (self.base/rel).write_bytes(original[rel]+b'\n# changed\n')
                try:
                    with self.assertRaisesRegex(ValueError,'operator pin'):attempt()
                finally:(self.base/rel).write_bytes(original[rel])
        # A different but self-consistent payload/public/bundle still must fail.
        payload=self.builder.unpack(original['package/0.tgz']);cfg=json.loads(payload['9.json']);cfg['unreviewed']=True
        payload['9.json']=json.dumps(cfg,sort_keys=True).encode();raw=self.builder.tarbytes(payload)
        public=json.loads(original['package/0.json']);public.update(payload_sha256=hashlib.sha256(raw).hexdigest(),payload_bytes=len(raw))
        from orchard_h10.common import canonical
        public['plan_sha256']=canonical(cfg)
        (self.base/'package/0.tgz').write_bytes(raw);write(self.base/'package/0.json',public)
        bundle=self.builder.bootstrap(original['package/BATCH.sh'].decode());bundle['0.json']=(self.base/'package/0.json').read_bytes()
        (self.base/'package/BATCH.sh').write_text(self.builder.batch(self.builder.tarbytes(bundle),public['token']))
        try:
            with self.subTest(base='self-consistent'),self.assertRaisesRegex(ValueError,'reviewed A4 payload'):attempt()
        finally:
            for rel in ('package/0.tgz','package/0.json','package/BATCH.sh'):(self.base/rel).write_bytes(original[rel])
        source=self.root/'tampered-source';(source/'u0').mkdir(parents=True)
        for p in (SRC/'u0').rglob('*'):
            if p.is_file():
                dest=source/'u0'/p.relative_to(SRC/'u0');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
        (source/'u0/a0.py').write_text('# altered\n')
        with self.subTest(extension='changed'),self.assertRaisesRegex(ValueError,'Extension inventory'):attempt(source=source)
        if not BEFORE:
            bad=copy.deepcopy(manifest);bad['base_pin']['inventory']['orchard_h10/job.py']='0'*64
            write(self.root/'bad-manifest.json',bad)
            with self.assertRaisesRegex(ValueError,'Alias base differs'):
                attempt(dict(self.options,manifest_path=self.root/'bad-manifest.json'))
            bad=copy.deepcopy(manifest);bad['patches']['03_production_integration.diff']['files']['u0/a19.py']['after_sha256']='0'*64
            write(self.root/'bad-manifest.json',bad)
            with self.assertRaisesRegex(ValueError,'Extension pins differ'):
                attempt(dict(self.options,manifest_path=self.root/'bad-manifest.json'))
        self.assertFalse((self.root/'refused').exists())

    def test_f3_binding_derivation_and_operations(self):
        helper=self.helpers();root=fresh();binding=copy.deepcopy(self.binding)
        art={k:binding[k] for k in ('step','config_sha256','base_identity','frame_layout')}
        for key,name in (('heads','heads.pt'),('full_weights','full_weights/full_weights.json')):
            art[key]={'path':'/scratch/jjyeung/'+binding['run']+'/'+binding['member_directory']+'/'+name}
        write(root/'artifact.json',art);(root/'done').write_text(binding['object']+' 4 '+'2'*64+'\n')
        prepared={k:root/k for k in ('config','receipt','data_receipt')}
        for k,p in prepared.items():write(p,{'base_identity':art['base_identity'],'frame_layout':art['frame_layout'],'config_sha256':art['config_sha256']})
        binding['preparation_sha256']={k:sha(p) for k,p in prepared.items()};binding['config_sha256']='FILL_FROM_ARTIFACT'
        write(root/'template.json',binding)
        got=helper.derive_binding(root/'template.json',root/'artifact.json',root/'done',prepared,root/'binding.json')
        self.assertEqual(got['config_sha256'],art['config_sha256']);self.assertEqual(got['prep_paths'],binding['prep_paths'])
        art['step']=400;write(root/'artifact.json',art)
        with self.assertRaisesRegex(ValueError,'step'):helper.derive_binding(root/'template.json',root/'artifact.json',root/'done',prepared,root/'bad.json')
        result=helper.operations(self.target,self.root/'binding.json',L/'out/operations',root/'ops')
        self.assertEqual(result['delivery_sha256'],sha(root/'ops/1.tgz'))
        members=self.builder.unpack((root/'ops/1.tgz').read_bytes())
        self.assertEqual(members['BATCH.sh'],(self.target/'package/BATCH.sh').read_bytes())
        for script in (root/'ops').glob('*.sh'):subprocess.run(['bash','-n',str(script)],check=True)
        for script,need in {
            'o_place.sh':['sha256sum -c SHA256','tar -xzf','test ! -e "$P"'],
            'o_pull_fill.sh':['part0$i-of-04','Boto:num_retries=0','"$D/d.py"','"$D/d2.py"','--step 600'],
            'o_cpu.sh':['sbatch --parsable','--partition=preempt','--cpus-per-task=8','--no-requeue','a/5.py'],
            'o_sub.sh':['"$D/check.py"','squeue -u jjyeung -p general','test ! -s "$P/a/9.txt"','3.py submit'],
            'o_fetch.sh':['3.py fetch --return-token']}.items():
            text=(root/'ops'/script).read_text()
            for term in need:self.assertIn(term,text)
        for name in ('d.py','d2.py','check.py'):ast.parse((root/'ops'/name).read_text(),feature_version=(3,6))
        self.assertLess((root/'ops/o_sub.sh').read_text().index('"$D/check.py"'),(root/'ops/o_sub.sh').read_text().index('3.py submit'))
        self.assertIn('unpack_return.py', (OUT/'kit_parity50/README.md').read_text())

    def test_f3_submit_pool_and_proof_refusals(self):
        helper=self.helpers();root=fresh();package=root/'package';(package/'a/c').mkdir(parents=True)
        for rel in ('0.json','0.tgz','a/6.py'):(package/rel).write_bytes((self.target/'package'/rel).read_bytes())
        write(package/'a/1.json',{});public=json.loads((package/'0.json').read_text())
        proof=dict(passed=True,entry_sequence_passed=True,bundle_guard_passed=True,plan=public['plan_sha256'],payload=public['payload_sha256'],inputs=sha(package/'a/1.json'),operator_sha256=sha(package/'a/6.py'),memory=dict(fits=True,basis='fixed_g3t_shapes',read_cache_bytes=12*1024**3))
        write(package/'a/c/CPU.json',proof)
        for name in ('dry.json','dry2.json'):write(package/'a'/name,dict(passed=True))
        pool=root/'pool';pool.mkdir();script=root/'check.py';script.write_text(helper.SUBMIT_CHECK)
        command=[sys.executable,'-I','-s','-B',str(script),str(package),str(pool)]
        self.assertEqual(subprocess.run(command,capture_output=True).returncode,0)
        bad=copy.deepcopy(proof);bad['memory'].pop('read_cache_bytes');write(package/'a/c/CPU.json',bad)
        failed=subprocess.run(command,capture_output=True,text=True);self.assertNotEqual(failed.returncode,0);self.assertIn('CPU memory proof differs',failed.stderr)
        write(package/'a/c/CPU.json',proof)
        # Exercise the exact boundary through the real checker with stat-only sizes.
        full=pool/'full';full.write_bytes(b'x');real_stat=Path.stat
        import runpy
        for size in (75000000,75000001):
            def measured(path,*args,**kwargs):
                return types.SimpleNamespace(st_size=size,st_mode=real_stat(path).st_mode) if path==full else real_stat(path,*args,**kwargs)
            with patch.object(Path,'stat',new=measured),patch.object(sys,'argv',[str(script),str(package),str(pool)]):
                if size==75000000:runpy.run_path(str(script),run_name='__main__')
                else:
                    with self.assertRaisesRegex(ValueError,'Return pool exceeds 75 MB'):runpy.run_path(str(script),run_name='__main__')

    def test_f4_gate_pins_adopted_settings_and_profile(self):
        kit=load('kit5',OUT/'kit_parity50/run.py')
        self.assertTrue(hasattr(kit,'validate_profile'),'GPU gate accepts an unbound read profile')
        helper=self.helpers()
        for processor in (False,True):
            root=fresh();target=self.target
            if processor:
                target=root/'built'
                self.builder.build(self.base,SRC,self.root/'binding.json',target,'ab0123456789',enable_extensions=True,processor_only=True,**self.options)
            package,public,cfg=helper.package_config(target)
            settings={key:cfg[key] for key in helper.PROFILE_KEYS};settings['arm']='own_depth'
            write(root/'prepared.json',settings)
            proof=dict(passed=True,plan=public['plan_sha256'],payload=public['payload_sha256'],ready=dict(settings=sha(root/'prepared.json')),operator_sha256=sha(package/'a/6.py'))
            write(root/'CPU.json',proof);write(root/'template.json',{})
            config=helper.gate(target,root/'prepared.json',root/'CPU.json',root/'template.json',root/'settings.json',root/'config.json')
            settings=json.loads((root/'settings.json').read_text());kit.validate_profile(config,settings)
            self.assertEqual(config['enable_caches'],[0] if processor else [0,1,2])
            for key,value in [('stage1_select_rule','null_argmax'),('perception_memo','off'),('read_cache_bytes',1),('save_own_depth',True)]:
                with self.subTest(processor=processor,key=key),self.assertRaises(ValueError):kit.validate_profile(config,dict(settings,**{key:value}))
            for key,value in [('enable_caches',[0,1]),('read_cache_bytes',1),('adoption_plan_sha256','')]:
                with self.subTest(config=key),self.assertRaises(ValueError):kit.validate_profile(dict(config,**{key:value}),settings)
            write(root/'prepared.json',dict(settings,read_cache_bytes=1))
            with self.assertRaisesRegex(ValueError,'proof differs'):
                helper.gate(target,root/'prepared.json',root/'CPU.json',root/'template.json',root/'badsettings',root/'badconfig')

    def test_f5_forecast_identifies_both_reads(self):
        for path in (OUT/'NOTE_FOR_CONT_OPS.md',OUT/'kit_parity50/README.md'):
            text=path.read_text()
            self.assertIn('Package D',text);self.assertIn('636-item',text)
            self.assertIn('7,351.824',text);self.assertIn('estimate',text.lower())
            self.assertIn('no ON route',text)

    def test_f7_refused_unpack_not_scoreable(self):
        for path in (OUT/'NOTE_FOR_CONT_OPS.md',OUT/'kit_parity50/README.md'):
            text=path.read_text()
            self.assertIn('refused unpack leaves',text.lower())
            self.assertIn('success output',text.lower())
        readme=(OUT/'kit_parity50/README.md').read_text()
        self.assertIn('--out "$LOCAL/step600/ret" > "$LOCAL/step600/unpack-success.json"',readme)
        self.assertIn('&&',readme)

if __name__=='__main__':unittest.main(verbosity=2)
