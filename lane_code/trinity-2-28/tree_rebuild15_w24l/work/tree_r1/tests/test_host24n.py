"""Relocated donor metadata stays authenticated; no production tensors are used."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from student_pilot import r1_handover as H, r1_persisted as P
from student_pilot.p3_provenance import digest, file_pin, load, pinned, write
from launch_r1 import p_export_receipt as E
from tests.test_host24j import config
from tests import test_host24l as host24l


def donor_fixture(root):
    def put(name, value):
        write(root/name, value)
        return file_pin(root/name)
    source = config()
    source.update(benchmark_scene_exclusions=None, routing_opener_init='keep')
    source['streams'] = {s:put(s+'.json', dict(database=dict(path=str(root/(s+'.db')),
        sha256=digest(s)), count=1)) for s in ('pose','vqa','routing','pointing')}
    ident = H.export_identity(source)
    preparation = put('preparation.json', dict(schema='c1-preparation-v1', config_sha256=ident,
        recipe=source['recipe'], training_mode='final', camera={}, streams={s:dict(receipt=p,
        database=load(pinned(p))['database'],count=1) for s,p in source['streams'].items()}))
    source['preparation'] = preparation
    run = dict(config=put('config.json',source), preparation=preparation,
        binding=put('binding.json',dict(config_sha256=ident, preparation=preparation,
                                      world_size=4,trainer_commit='fixture')))
    heads = put('heads.json',dict(synthetic=True))
    shard = put('export/shard.json',dict(synthetic_weights=True))
    index = put('export/index.json',dict(shards=['shard.json']))
    manifest = put('export/manifest.json',dict(index=dict(name='index.json',sha256=index['sha256']),
        files=[dict(name='shard.json',sha256=shard['sha256'])]))
    artifact = put('artifact.json',dict(schema='carrier-c1-artifact-v1',step=400,config_sha256=ident,
                                      heads=heads,full_weights=manifest))
    receipt = E.produce(run,artifact,root/'receipt.json',job_id='fixture',trainer_commit='fixture')
    cfg = deepcopy(source)
    cfg.update(init_artifact=dict(artifact=artifact), r1_training=dict(p_run=deepcopy(run),
        donor_config_sha256=ident, handover_receipt=receipt, proof_mode='q',persisted_files={}))
    return cfg, load(pinned(artifact))


class DonorPins(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='pins24n_'))
        self.cfg, self.artifact = donor_fixture(self.root/'donor')

    def localize(self):
        run = self.cfg['r1_training']['p_run']
        old = run['preparation']
        target = self.root/'localized/preparation.json'
        target.parent.mkdir()
        target.write_bytes(Path(old['path']).read_bytes())
        run['preparation'] = file_pin(target)
        self.cfg['r1_training']['persisted_files'][old['sha256']] = str(target)
        return target

    def call(self, module=H):
        with P.proof_scope():
            return module.donor(self.cfg, self.artifact)

    def rewrite_metadata(self, key, value):
        run = self.cfg['r1_training']['p_run']
        path = self.root/(key+'_changed.json')
        write(path, value)
        run[key] = file_pin(path)
        receipt = load(pinned(self.cfg['r1_training']['handover_receipt']))
        receipt['pins'][key] = run[key]
        receipt_path = self.root/(key+'_receipt.json')
        write(receipt_path,receipt)
        self.cfg['r1_training']['handover_receipt'] = file_pin(receipt_path)

    def isolated_binding(self, changed):
        """Authenticate altered donor metadata, then isolate each equality in _donor."""
        self.localize()
        run = self.cfg['r1_training']['p_run']
        source, bound = (load(pinned(run[k])) for k in ('config','binding'))
        # Export identity omits preparation, so this changes only the tested pin.
        for key, value in (('config', source), ('binding', bound)):
            if key != changed:
                value['preparation'] = deepcopy(run['preparation'])
            write(self.root/(key+'_isolated.json'),value)
            run[key] = file_pin(self.root/(key+'_isolated.json'))
        self.cfg['r1_training'].pop('persisted_files')
        return run

    def base(self):
        path = Path(__file__).resolve().parents[2]/'tree_r1_base/student_pilot/r1_handover.py'
        if not path.is_file():
            self.skipTest('Untouched base tree is required for the failing-before comparison')
        spec = importlib.util.spec_from_file_location('student_pilot.handover24n_base',path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def exercise_comparison(self, key):
        run = self.isolated_binding(key)
        # The final closure check is independent and covered unmocked below.
        with P.proof_scope(), patch.object(P,'verify',return_value={}):
            with self.assertRaisesRegex(ValueError,'P_EXPORT_RUN_BINDING_MISMATCH'):
                self.base()._donor(self.cfg,self.artifact)
            H._donor(self.cfg,self.artifact)
            saved_run = deepcopy(run)
            original = deepcopy(run['preparation'])
            # Different, correctly hashed bytes must fail the binding comparison.
            prep = load(pinned(original)); prep['different_bytes'] = True
            write(self.root/'different.json',prep)
            run['preparation'] = file_pin(self.root/'different.json')
            other = 'binding' if key == 'config' else 'config'
            metadata = load(pinned(run[other]))
            metadata['preparation'] = deepcopy(run['preparation'])
            write(self.root/'other_hash.json', metadata)
            run[other] = file_pin(self.root/'other_hash.json')
            with self.assertRaisesRegex(ValueError,'P_EXPORT_RUN_BINDING_MISMATCH'):
                H._donor(self.cfg,self.artifact)
            # The stated hash is unchanged, but the staged bytes have been corrupted.
            run.clear(); run.update(saved_run)
            Path(original['path']).write_text('{}')
            with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):
                H._donor(self.cfg,self.artifact)

    def test_source_preparation_comparison(self):
        self.exercise_comparison('config')

    def test_binding_preparation_comparison(self):
        self.exercise_comparison('binding')

    def test_native_persisted_donor_accepts_relocation(self):
        before = self.call()
        self.localize()
        self.assertEqual(before,self.call())
        with P.proof_scope(), self.assertRaisesRegex(ValueError,'P_EXPORT_RUN_BINDING_MISMATCH'):
            self.base().donor(self.cfg,self.artifact)

    def test_native_persisted_donor_refuses_corrupt_local_bytes(self):
        self.localize().write_text('{}')
        with self.assertRaisesRegex(ValueError,'P_EXPORT_HANDOVER_FILE_MISMATCH:preparation'):
            self.call()

    def test_native_persisted_donor_refuses_other_hash(self):
        path = self.localize()
        path.write_text('{}')
        self.cfg['r1_training']['p_run']['preparation'] = file_pin(path)
        with self.assertRaisesRegex(ValueError,'P_EXPORT_HANDOVER_PIN_MISMATCH:preparation'):
            self.call()

    def test_schema_still_refuses(self):
        prep = load(pinned(self.cfg['r1_training']['p_run']['preparation']))
        prep['schema'] = 'foreign'
        # Bind matching pins everywhere so the schema alone is false.
        self.rewrite_metadata('preparation',prep)
        run = self.cfg['r1_training']['p_run']
        for key in ('config','binding'):
            value=load(pinned(run[key]));value['preparation']=run['preparation']
            self.rewrite_metadata(key,value)
        with self.assertRaisesRegex(ValueError,'P_EXPORT_RUN_BINDING_MISMATCH'):
            self.call()

    def test_binding_and_preparation_identity_still_refuse(self):
        for key in ('binding','preparation'):
            with self.subTest(key=key):
                self.setUp()
                value=load(pinned(self.cfg['r1_training']['p_run'][key]))
                value['config_sha256']='0'*64
                self.rewrite_metadata(key,value)
                with self.assertRaisesRegex(ValueError,'P_EXPORT_HANDOVER_RUN_BINDING_MISMATCH'):
                    self.call()

    def test_non_path_pin_fields_still_refuse(self):
        for key in ('config','binding'):
            for mutation in ('extra', 'missing_path', 'missing_hash', 'empty_path', 'non_dict'):
                with self.subTest(key=key,mutation=mutation):
                    self.setUp()
                    run=self.isolated_binding(key)
                    value=load(pinned(run[key]))
                    if mutation=='extra':value['preparation']['extra']='not a pin'
                    elif mutation=='missing_path':value['preparation'].pop('path')
                    elif mutation=='missing_hash':value['preparation'].pop('sha256')
                    elif mutation=='empty_path':value['preparation']['path']=''
                    else:value['preparation']=None
                    write(self.root/'extra.json',value);run[key]=file_pin(self.root/'extra.json')
                    with P.proof_scope(),patch.object(P,'verify',return_value={}), \
                            self.assertRaisesRegex(ValueError,'P_EXPORT_RUN_BINDING_MISMATCH'):
                        H._donor(self.cfg,self.artifact)


class LocalizedQ(unittest.TestCase):
    setUp = host24l.Host24L.setUp
    fixture = host24l.Host24L.fixture
    pin = host24l.Host24L.pin
    repin = host24l.Host24L.repin
    host = host24l.Host24L.host
    dependencies = host24l.Host24L.dependencies
    def run_native_q(self, *, fresh=False):
        from launch_r1 import production_proof as proof
        cfg, request = self.fixture()
        cfg['preparation'] = self.pin('q_preparation.json', dict(schema='c1-preparation-v1',
            camera={}, streams={name:dict(receipt=pin) for name,pin in cfg['streams'].items()}), stage=True)
        donor, artifact = donor_fixture(self.area/'donor')
        value=donor['r1_training']
        if fresh:
            value.update(init_policy=P.INIT_POLICY, proof_mode='train')
        receipt=load(pinned(value['handover_receipt']))
        paths={}
        for key,pin in receipt['pins'].items():
            paths[pin['sha256']]=self.pin('donor_'+pin['sha256'],Path(pin['path']).read_bytes(),stage=True)['path']
        handover=self.pin('donor_h.json',Path(value['handover_receipt']['path']).read_bytes(),stage=True)
        cfg['r1_training'].update(value, handover_receipt=handover, persisted_files=paths)
        cfg['r1_training']['p_run']={key:dict(pin,path=paths[pin['sha256']]) for key,pin in value['p_run'].items()}
        cfg['init_artifact']=dict(artifact=dict(donor['init_artifact']['artifact'],
            path=paths[donor['init_artifact']['artifact']['sha256']]))
        cfg['routing_opener_init']='keep'
        self.repin(cfg,request)
        native_donor, native_verify, native_bind, native_admission = H.donor, P.verify, H.bind_target, P.admission
        native_compare = H.compare_configs
        # Capacity producers retain the config; native donor/config/mapping gates run.
        def prepare(pin, directory, *args, **kwargs):
            write(directory/'config.json', load(pinned(pin)))
            return dict(config=file_pin(directory/'config.json'))
        def populate(current, directory):
            write(directory/'config.json', current)
            return file_pin(directory/'config.json')
        with self.dependencies(), patch.object(H,'donor',native_donor), \
                patch.object(P,'verify',native_verify), patch.object(H,'bind_target',native_bind), \
                patch.object(P,'admission',native_admission), patch.object(H,'compare_configs',native_compare), \
                patch('student_pilot.s1_admission.admit',side_effect=prepare), \
                patch('student_pilot.r1_population.bind_prepared',side_effect=populate):
            result=proof.run(request,self.root)
        self.host(result)
        self.assertIn('persisted_handover',result['steps'])
        self.assertIn('r1_loader.production_audit',result['steps'])
        final=load(pinned(result['config']))
        self.assertNotEqual(final['r1_training']['p_run']['preparation']['path'],
            load(pinned(value['p_run']['config']))['preparation']['path'])

        self.assertEqual(result['absolute_resume_step'], 0 if fresh else 400)
        self.assertEqual(result['init_milestone'], 400)

    def test_q_reaches_past_native_handover(self):
        self.run_native_q()

    def test_q_fresh_training_reaches_past_native_handover(self):
        self.run_native_q(fresh=True)
