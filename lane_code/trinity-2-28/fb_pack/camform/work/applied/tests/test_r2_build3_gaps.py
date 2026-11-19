"""Real-input refusal paths that need neither full stores nor a model forward."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
from launch_r2 import host as H, build as B
from student_pilot.p3_provenance import file_pin, load, write
from tests.test_r2_data_path import PROOFS, directory, fixture, manifest, LANE


class Gaps(unittest.TestCase):
    def test_host_packet_refusals(self):
        from tests.test_r2_portable import fixture as binding_fixture
        from student_pilot.r2_config import configure
        from tests.test_gf1 import settings
        from tests.test_r2_build3 import Build3
        Build3().test_native_prepare_and_every_rank_encode()
        root=directory()
        original_packet=load(PROOFS/'B3_NATIVE_JOB_PROOF.json')['packet']
        base=load(original_packet['path'])
        cfg=load(base['configuration']['path'])
        with self.assertRaisesRegex(ValueError,'Missing bound kit configuration'):
            H.run_packet(root,original_packet,full=False)
        write(root/'k/launch.json',dict(config=dict(file=base['configuration']['path'],sha256='0'*64)))
        with self.assertRaisesRegex(ValueError,'Packet configuration differs'):
            H.run_packet(root,original_packet,full=False)
        number=0
        def invoke(packet,config=None,full=False,reason=''):
            nonlocal number
            number+=1
            packet=deepcopy(packet)
            if config is not None:
                path=root/f'c{number}.json';write(path,config);packet['configuration']=file_pin(path)
            (root/'k').mkdir(exist_ok=True)
            (root/'k/launch.json').write_text(json.dumps(dict(config=dict(file=packet['configuration']['path'],sha256=packet['configuration']['sha256']))))
            path=root/f'p{number}.json';write(path,packet)
            with self.assertRaisesRegex(ValueError,reason):H.run_packet(root,file_pin(path),full=full)
        invoke({**base,'pose_sources':[base['pose_sources'][0],base['configuration']]},reason='Pose manifests')
        write(root/'plain.json',{})
        invoke({**base,'counts':file_pin(root/'plain.json'),'real_proof':file_pin(root/'plain.json')},full=True,reason='sealed source')
        binding,_=binding_fixture(root)
        bound_cfg={**cfg,'r2_build2':binding}
        invoke(base,bound_cfg,reason='counts differ')
        counted={**base,'counts':binding['counts']}
        invoke(counted,bound_cfg,reason='type indices')
        invoke({**counted,'output':'../escape'},{**bound_cfg,'r2_sampling':{}},reason='type indices')
        invoke({**counted,'output':'../escape'},{**bound_cfg,'r2_sampling':{'bound':True}},reason='new folder')
        invoke(base,{**cfg,'geometry_connector':'gf1'},reason='dense manifest')
        write(root/'dense_bad.json',{'synthetic':True})
        invoke({**base,'dense':file_pin(root/'dense_bad.json')},{**cfg,'geometry_connector':'gf1'},reason='real dense')
        write(root/'dense.json',dict(schema='r2-dense-manifest-v1',reconstruct_then_subsample=True,clips={'fixture':[]}))
        packet={**base,'dense':file_pin(root/'dense.json')}
        invoke(packet,{**cfg,'geometry_connector':'gf1'},reason='tower assets')
        write(root/'assets.json',settings())
        parent=load(LANE/'work/kit07ca49df_meta/m/k/b02e4385.json')
        gf=configure(parent,'gf1',dense_manifest=packet['dense'], init_pin=INIT_PIN)
        invoke({**packet,'geometry_assets':file_pin(root/'assets.json'),'output':'../escape'},gf,reason='new folder')
        # Reach native arm binding in the bounded metadata fixture; the unsafe
        # output path then refuses before a store or frozen tower is opened.
        local_arm={key:value for key,value in gf.items() if key not in ('r2_all_stream_exclusions','r2_build2')}
        invoke({**packet,'geometry_assets':file_pin(root/'assets.json'),'output':'../escape'},local_arm,reason='new folder')
        invoke({**base,'output':'../escape'},reason='new folder')
        # The real producer sees valid envelopes but no frame-root mapping.
        missing={**base,'output':'missing','init_archive':None}
        with patch.dict(os.environ,{'STUDENT_FRAME_ROOT_MAP':'{}'}):
            invoke(missing,reason='Missing real RGB')
        with self.assertRaisesRegex(ValueError,'member inventory'):
            H.stage_init({},root/'a',{},max_member_bytes=0)

    def test_real_dense_limit_and_entry_inventory(self):
        from student_pilot.r2_materialize import materialize
        from launch_r2.entry import host_receipt
        from launch_r2.runtime import obligations
        from student_pilot.p3_provenance import digest
        root=directory();row=fixture(root);mp=manifest(root/'m',[row])
        with patch.dict(os.environ,{'STUDENT_FRAME_ROOT_MAP':json.dumps({'/logical/r2':str(root/'frames')})}):
            with self.assertRaisesRegex(ValueError,'limit: dense'):
                materialize([mp],root/'s',limits={'vqa':1000000,'membership':1000000,'dense':1})
        cfg=dict(world_size=4,streams={'vqa':{}})
        write(root/'c.json',cfg)
        packet=dict(configuration=file_pin(root/'c.json'))
        write(root/'p.json',packet)
        value=dict(schema='r2-host-preparation-v1',full_store=True,source_revision='sha256:'+'a'*64,
            packet_digest=digest(packet),statements=[{**s,'reached':True} for s in obligations()],
            config=cfg,bound_config_sha256=packet['configuration']['sha256'],prepared_config_sha256=digest(cfg),
            first_batch=[dict(rank=r,stream='vqa',tokens=1,forward=False) for r in range(4)],
            unit_contract_fixture=True,production_authorized=False)
        from launch_r2.checklist import ITEMS
        value['checks'] = {}
        for item in ITEMS:
            path = root/('check'+str(item)+'.json')
            write(path, dict(item=item, status='PASS'))
            value['checks'][str(item)] = file_pin(path)
        def invoke(v):
            receipt=root/'receipt.json';receipt.write_text(json.dumps(v))
            launch=dict(prepared=file_pin(receipt),inputs=file_pin(root/'p.json'),source_revision=value['source_revision'],
                        config=dict(file='c.json',sha256=packet['configuration']['sha256']))
            return host_receipt(root,launch)
        self.assertEqual(invoke(value),value)
        for change,reason in [(dict(full_store=False),'statement obligations'),(dict(first_batch=[]),'every rank'),
                              (dict(bound_config_sha256='0'*64),'configuration'),
                              (dict(prepared_config_sha256='0'*64),'configuration')]:
            with self.assertRaisesRegex(ValueError,reason):invoke({**value,**change})
        with self.assertRaisesRegex(ValueError,'required checks'):invoke({**value,'checks':{}})
        write(root/'refused.json',dict(item=1,status='REFUSE'))
        with self.assertRaisesRegex(ValueError,'did not pass'):
            invoke({**value,'checks':{**value['checks'],'1':file_pin(root/'refused.json')}})

    def test_worker_script_and_module_restoration(self):
        from launch_r2 import worker
        with patch.object(sys,'argv',['w',str(directory()),'t','1']):
            with self.assertRaisesRegex(ValueError,'arm'):runpy.run_path(worker.__file__,run_name='__main__')
        # The final-kit test stages the current source before this check.
        from tests.test_r2_build import inputs
        kit=directory()/'a';B.build(LANE/'work/kit07ca49df_meta/m',kit,connector='none',records=inputs(), init_pin=INIT_PIN)
        with patch.dict(sys.modules,{'v':object()}):
            previous=sys.modules['v'];B.verify(kit);self.assertIs(sys.modules['v'],previous)

from tests.r2_init_fixture import PIN as INIT_PIN
