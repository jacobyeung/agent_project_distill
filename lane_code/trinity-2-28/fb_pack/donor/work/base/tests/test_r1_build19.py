"""Persisted provenance, deferred exports and actual sealed bank gateway twins."""
from pathlib import Path
from copy import deepcopy
import os, json, unittest
from student_pilot.p3_provenance import load, file_pin, digest
from student_pilot import r1_components as C, r1_training as T, r1_persisted as P, r2_policy as R
from tests.test_r2_build_n1 import write

L=Path(os.environ.get('R2_LANE_ROOT',Path(__file__).resolve().parents[3]))


def bank_read(root,artifact,bank):
    from launch_r2 import build as B
    root=root/'g'
    root.mkdir(parents=True,exist_ok=True);(root/'b').mkdir(exist_ok=True);(root/'k').mkdir(exist_ok=True)
    (root/'b/wh.json').write_bytes((B.TREE/'launch_s1/b/wh.json').read_bytes())
    (root/'job.sh').write_text('#!/bin/bash\nexit 2\n')
    def save(v):
        raw=B.capsule_json(v);h=__import__('hashlib').sha256(raw).hexdigest();p=root/'k'/(h+'.json');p.write_bytes(raw)
        return dict(path='k/'+p.name,sha256=h)
    items=[dict(id='fixture',question_type='camera_displacement',question='How far in metres?',venue='fixture')]
    itempin=write(root.parent/(root.name+'_items.json'),items)
    catalog=R.seal_catalog({bank:itempin})
    cfg=dict(init_artifact=dict(artifact=save(artifact)),r1_training=dict(registry=save(R.slots())),
        r2_evaluation=dict(catalog=save(catalog),camera_routing=True))
    pin=save(cfg)
    (root/'k/launch.json').write_bytes(B.capsule_json(dict(config=dict(file=pin['path'],sha256=pin['sha256']))))
    (root/'k/0.json').write_bytes(B.capsule_json(dict(commit='a'*40,trainer=dict(file=pin['path'],sha256=pin['sha256']),record=dict(file=pin['path'],sha256=pin['sha256']))))
    files=[root/'job.sh',*list((root/'b').rglob('*')),*list((root/'k').rglob('*'))]
    (root/'SHA256SUMS.txt').write_text(''.join(file_pin(p)['sha256']+'  '+str(p.relative_to(root))+'\n' for p in files if p.is_file()))
    (root/'ANON_OK.json').write_text(json.dumps(dict(status='CLEAN',hits=0,manifest_sha256=file_pin(root/'SHA256SUMS.txt')['sha256'])))
    return R.read_bank(itempin,kit_root=root)


class Components19(unittest.TestCase):
    def setUp(self):
        from tests.test_r1_build16 import Build16
        Build16.setUp(self)
        self.root=Path(os.environ['R2_PROOFS'])/'components19'/self._testMethodName
        self.root.mkdir(parents=True,exist_ok=True)
        self.cfg=load(L/'work/build19/proofs/native/600/request_config.json')

    def tearDown(self):
        self.open_patch.stop()

    def records(self,cfg=None):
        cfg=self.cfg if cfg is None else cfg
        with P.proof_scope():return T.training_components(cfg['r1_training']['registry'],cfg)

    def card(self,**changes):
        cfg=deepcopy(self.cfg);card=load(cfg['r1_training']['mix']['path']);card.update(changes)
        cfg['r1_training']['mix']=write(self.root/'card.json',card);return cfg

    def test_verified_export_and_successor(self):
        for cfg in (self.cfg,self.card(leg='R2',successor_of='R1')):
            records=self.records(cfg)
            self.assertEqual(set(records),set((*R.LINEAGE,*R.EXTERNAL,*R.NEW)))
            self.assertTrue(all(v['status']=='DEFERRED' for v in records.values()))
            self.assertEqual(records['data_rows_r2']['record']['unproven']['unresolved_v7_rows'],119375)
        self.assertIsNone(C.deferred(self.cfg,'native_evaluation'))
        cfg=deepcopy(self.cfg);cfg['r1_training']['proof_mode']='train';self.assertEqual(len(self.records(cfg)),9)
        cfg=load(L/'work/build19/proofs/native/400/request_config.json');self.assertEqual(len(self.records(cfg)),9)

    def test_complete_records_preserve_gate(self):
        from tests.test_r2_policy import evidence
        cfg=self.card(vehicle='P');cfg['r1_training']['registry']=evidence(self.root/'complete')
        self.assertEqual(len(self.records(cfg)),8)
        self.assertTrue(all(v['status']=='VERIFIED' for v in C.artifact_status(cfg).values()))

    def test_other_cards_and_parent_refuse(self):
        for changes in (dict(vehicle='P'),dict(leg='other'),dict(leg='other',successor_of='other')):
            cfg=self.card(**changes)
            with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):self.records(cfg)
        cfg=deepcopy(self.cfg);cfg['init_artifact']['artifact']=file_pin(L/'work/n1fix2/inputs/init_artifact.json')
        with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):self.records(cfg)
        cfg=deepcopy(self.cfg);cfg['r1_training'].pop('handover_receipt')
        with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):self.records(cfg)
        self.assertIsNone(C.deferred({}))
        cfg=deepcopy(self.cfg);cfg['r1_training']['proof_mode']='other';self.assertIsNone(C.deferred(cfg))

    def test_receipt_and_lineage_refuse(self):
        cfg=deepcopy(self.cfg);cfg['r1_training']['handover_receipt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'HANDOVER_RECEIPT_UNVERIFIED'):self.records(cfg)
        cfg=self.donor_variant(output=str(self.root/'other'))
        with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):self.records(cfg)

    def donor_variant(self,**changes):
        from student_pilot.r1_handover import export_identity
        cfg=deepcopy(self.cfg);v=cfg['r1_training'];receipt=load(v['handover_receipt']['path'])
        source=load(v['p_run']['config']['path']);source.update(changes);identity=export_identity(source)
        prep=load(v['p_run']['preparation']['path']);prep['config_sha256']=identity
        source['preparation']=write(self.root/'prep.json',prep)
        bound=load(v['p_run']['binding']['path']);bound.update(config_sha256=identity,preparation=source['preparation'])
        checkpoint=load(v['p_run']['checkpoint']['path']);checkpoint['binding']=bound
        artifact=load(cfg['init_artifact']['artifact']['path']);artifact['config_sha256']=identity
        for name,pin in dict(config=write(self.root/'donor.json',source),preparation=source['preparation'],
                binding=write(self.root/'binding.json',bound),checkpoint=write(self.root/'checkpoint.json',checkpoint),
                artifact=write(self.root/'artifact.json',artifact)).items():
            v['persisted_files'].pop(receipt['pins'][name]['sha256'],None)
            receipt['pins'][name]=pin
            if name=='artifact':cfg['init_artifact']['artifact']=pin
            else:v['p_run'][name]=pin
        v['handover_receipt']=write(self.root/'receipt.json',receipt)
        return cfg

    def test_wrong_parent_refuses(self):
        cfg=self.donor_variant(init_artifact=dict(artifact=dict(path='missing',sha256='0'*64)))
        with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):self.records(cfg)

    def test_rows_record_is_required_and_pinned(self):
        cfg=deepcopy(self.cfg);cfg['r1_training'].pop('component_rows')
        with self.assertRaisesRegex(ValueError,'ROWS_RECORD_REQUIRED'):self.records(cfg)
        for change in (dict(schema='other'),dict(status='CLEAN'),dict(proven={}),dict(unproven={}),dict(inputs=[])):
            cfg=deepcopy(self.cfg);r=load(cfg['r1_training']['component_rows']['path']);r.update(change)
            cfg['r1_training']['component_rows']=write(self.root/'rows.json',r)
            with self.assertRaisesRegex(ValueError,'ROWS_RECORD_INVALID'):self.records(cfg)
        cfg=deepcopy(self.cfg);r=load(cfg['r1_training']['component_rows']['path']);r['inputs'][0]['sha256']='0'*64
        cfg['r1_training']['component_rows']=write(self.root/'rows.json',r)
        with self.assertRaises(ValueError):self.records(cfg)

    def test_registry_classification_still_refuses(self):
        cfg=deepcopy(self.cfg);r=load(cfg['r1_training']['registry']['path']);r['init_m544']['phase']='other'
        cfg['r1_training']['registry']=write(self.root/'registry.json',r)
        with self.assertRaisesRegex(ValueError,'slot was reclassified'):self.records(cfg)

    def test_official_and_dev_actual_gateway(self):
        artifact=dict(schema='carrier-c1-artifact-v1',r1_progress=dict(step=600),component_evidence=self.records())
        for bank in R.SCOPE:
            with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_DEFERRED:.*:official-item-read'):
                bank_read(self.root/bank,artifact,bank)
        for bank in C.DEV:
            items,receipt=bank_read(self.root/bank,artifact,bank)
            self.assertEqual(len(items),1);self.assertEqual(receipt['label'],'paired-comparison only')
        for name,changed in [('foreign_schema',dict(artifact,schema='other')),('non_N',dict(artifact,r1_progress=None)),
                             ('no_deferral',dict(artifact,component_evidence={'init_m544':dict(status='VERIFIED')}))]:
            with self.assertRaisesRegex(ValueError,'Missing component evidence: init_m544'):
                bank_read(self.root/name,changed,'dev-S1')
        for name in (*R.LINEAGE,*R.EXTERNAL,*R.NEW):
            with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_DEFERRED:'+name):
                C.guard(dict(component_evidence={name:dict(status='DEFERRED')}),['VSI-Bench'],'handover')
        with self.assertRaisesRegex(ValueError,'COMPONENT_BANK_SCOPE_UNKNOWN'):C.guard(artifact,['unknown'],'reader')
        with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_SLOTS_DIFFER'):
            C.guard(dict(component_evidence={'init_m544':dict(status='VERIFIED')}),['VSI-Bench'],'reader')
        with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_MISSING:init_m544'):
            C.guard(dict(r1_progress=dict(step=600)),['VSTI'],'reader')

    def test_selection_and_inherited_export_status(self):
        from student_pilot.r2_contract import selected_init
        artifact=dict(component_evidence=self.records())
        pin=write(self.root/'artifact.json',artifact)
        selection=dict(schema='r2-init-selection-v1',artifact=pin,identity=dict(self.cfg['r2_identity']['init'],artifact_sha256=pin['sha256']))
        with self.assertRaisesRegex(ValueError,'DEFERRED:.*:init-selection'):selected_init(write(self.root/'selection.json',selection))
        selection['banks']=['dev-S1'];self.assertEqual(selected_init(write(self.root/'selection.json',selection)),selection['identity'])
        with self.assertRaisesRegex(ValueError,'DEFERRED:.*:init-selection'):
            selected_init(write(self.root/'selection.json',selection),official=True)
        with self.assertRaisesRegex(ValueError,'ARTIFACT_REQUIRED'):
            selected_init(write(self.root/'selection.json',dict(schema='r2-init-selection-v1')),official=True)
        self.assertEqual(C.artifact_status(dict(init_artifact=dict(artifact=pin))),artifact['component_evidence'])
        self.assertEqual(C.artifact_status({}),{})
        with P.proof_scope():self.assertEqual(C.artifact_status(self.cfg),self.records())
        with self.assertRaisesRegex(ValueError,'DEFERRED:.*:official-export'):
            C.artifact_status(dict(init_artifact=dict(artifact=pin),r2_evaluation=dict(catalog='required')))

    def test_handover_carries_deferred_artifact(self):
        cfg=self.donor_variant();v=cfg['r1_training'];r=load(v['handover_receipt']['path'])
        artifact=load(cfg['init_artifact']['artifact']['path']);artifact['component_evidence']=self.records()
        ap=write(self.root/'n_export.json',artifact);cfg['init_artifact']['artifact']=ap;r['pins']['artifact']=ap
        v['handover_receipt']=write(self.root/'h_pending.json',r)
        with self.assertRaisesRegex(ValueError,'DEFERRED:.*:official-handover'):P.admission(cfg,official=True)

    def test_native_export_contains_slots(self):
        from student_pilot import carrier_c1_run as run
        from tests.test_carrier_c1 import fixture
        from tests.test_carrier_c1_run import RunnerTests
        from unittest.mock import patch
        cfg=deepcopy(self.cfg)
        # Export publication uses a tiny model and CPU collectives. The status
        # producer authenticates the unchanged persisted P closure above.
        model,_,_=fixture(4,training_mode='final')
        cfg.pop('code',None);cfg.pop('checkpoint_disk_guard',None)
        from student_pilot.r1_handover import bind_target
        cfg=bind_target(cfg,self.root/'mapping.json')
        cfg['preparation']=write(self.root/'prepared.json',dict(schema='c1-preparation-v1',component_evidence=self.records(),r1_training=cfg['r1_training']))
        original_open=Path.open
        def opened(path,mode='r',*a,**kw):return original_open(path,mode.replace('x','w') if path.is_relative_to(self.root) else mode,*a,**kw)
        original_mkdir=Path.mkdir
        def mkdir(path,mode=0o777,parents=False,exist_ok=False):return original_mkdir(path,mode,parents,True if path.is_relative_to(self.root) else exist_ok)
        with RunnerTests().local_collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()),patch.object(Path,'open',opened),patch.object(Path,'mkdir',mkdir):
            run.export(self.root/'export',model,model,cfg,600)
        exported=load(self.root/'export/artifact.json')
        self.assertEqual(exported['component_evidence'],self.records())
        with self.assertRaisesRegex(ValueError,'DEFERRED:.*:official-item-read'):
            bank_read(self.root/'official',exported,'VSI-Bench')
        self.assertEqual(len(bank_read(self.root/'development',exported,'dev-S1')[0]),1)
