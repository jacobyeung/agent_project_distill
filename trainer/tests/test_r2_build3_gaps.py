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
from tests.test_r2_data_path import directory, fixture, manifest, LANE


class Gaps(unittest.TestCase):
    def test_host_packet_refusals(self):
        from tests.test_r2_portable import fixture as binding_fixture
        from student_pilot.r2_config import configure
        from tests.test_gf1 import settings
        root=directory()
        base=load(load(LANE/'out/B3_NATIVE_JOB_PROOF.json')['packet']['path'])
        cfg=load(base['configuration']['path'])
        number=0
        def invoke(packet,config=None,full=False,reason=''):
            nonlocal number
            number+=1
            packet=deepcopy(packet)
            if config is not None:
                path=root/f'c{number}.json';write(path,config);packet['configuration']=file_pin(path)
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
        gf=configure(parent,'gf1',dense_manifest=packet['dense'])
        invoke({**packet,'geometry_assets':file_pin(root/'assets.json'),'output':'../escape'},gf,reason='new folder')
        invoke({**base,'output':'../escape'},reason='new folder')
        # The real producer sees valid envelopes but no frame-root mapping.
        missing={**base,'output':'missing','init_archive':None}
        with patch.dict(os.environ,{'STUDENT_FRAME_ROOT_MAP':'{}'}):
            invoke(missing,reason='Missing real RGB')
        with self.assertRaisesRegex(ValueError,'member inventory'):
            H.stage_init({},root/'a',{},max_member_bytes=0)

    def test_real_dense_limit_and_entry_inventory(self):
        from student_pilot.r2_materialize import materialize
        from tests.test_r2_portable import fixture as binding_fixture
        from launch_r2.closure import transport
        from launch_r2.entry import main
        root=directory();row=fixture(root);mp=manifest(root/'m',[row])
        with patch.dict(os.environ,{'STUDENT_FRAME_ROOT_MAP':json.dumps({'/logical/r2':str(root/'frames')})}):
            with self.assertRaisesRegex(ValueError,'limit: dense'):
                materialize([mp],root/'s',limits={'vqa':1000000,'membership':1000000,'dense':1})
        bindings,_=binding_fixture(root)
        (root/'b').mkdir();(root/'k').mkdir()
        (root/'b/wh.json').write_bytes((B.TREE/'launch_s1/b/wh.json').read_bytes())
        (root/'job.sh').write_text('#!/bin/bash\nexit 1\n')
        def put(raw,suffix):
            h=hashlib.sha256(raw).hexdigest();path=root/'k'/(h+suffix);path.write_bytes(raw)
            return dict(path='k/'+path.name,sha256=h)
        moved,_=transport(bindings,put)
        write(root/'k/a.json',{'r2_build2':moved})
        launch={'config':{'file':'k/a.json'},'inputs':None}
        write(root/'k/launch.json',launch)
        # Scan only the kit surface; this fixture's row envelopes live beside it.
        # Move the small kit surface to a new local folder, without any data store.
        kit=root/'kit';kit.mkdir();(kit/'b').mkdir();(kit/'k').mkdir()
        for name in ('b','k'):
            for path in (root/name).iterdir():(kit/name/path.name).write_bytes(path.read_bytes())
        (kit/'job.sh').write_bytes((root/'job.sh').read_bytes())
        with self.assertRaisesRegex(ValueError,'input inventory'):main(kit,'t')
        write(kit/'k/f.json',{})
        (kit/'k/launch.json').write_text(json.dumps({**launch,'inputs':{'path':'k/f.json','sha256':file_pin(kit/'k/f.json')['sha256']}}))
        with self.assertRaisesRegex(ValueError,'Missing pose'):main(kit,'t')
        from launch_r2.entry import host_receipt
        from launch_r2.runtime import obligations
        from student_pilot.p3_provenance import digest
        cache=kit/'o/ee000004';cache.mkdir(parents=True)
        value=dict(schema='r2-host-preparation-v1',full_store=True,source_revision='sha256:'+'a'*64,
            packet_digest=digest({}),statements=[{**s,'reached':True} for s in obligations()],
            config=dict(world_size=4,streams={'vqa':{}}),
            first_batch=[dict(rank=r,stream='vqa',tokens=1,forward=False) for r in range(4)],
            unit_contract_fixture=True,production_authorized=False)
        receipt=cache/'0.json'
        def bind(value):
            receipt.write_text(json.dumps(value))
            current={**load(kit/'k/launch.json'),'prepared':dict(path='o/ee000004/0.json',sha256=file_pin(receipt)['sha256']),
                     'source_revision':value['source_revision'],'production_authorized':False}
            (kit/'k/launch.json').write_text(json.dumps(current))
            return current
        current=bind(value)
        self.assertEqual(host_receipt(kit,current),value)
        self.assertEqual(main(kit,'p'),value)
        with self.assertRaisesRegex(ValueError,'production authorization'):main(kit,'t')
        with self.assertRaisesRegex(ValueError,'statement obligations'):host_receipt(kit,bind({**value,'full_store':False}))
        with self.assertRaisesRegex(ValueError,'every rank'):host_receipt(kit,bind({**value,'first_batch':[]}))
        current=bind(value);current['production_authorized']=True
        (kit/'k/launch.json').write_text(json.dumps(current))
        write(kit/'k/4.json',dict(allow_until_utc='2099-01-01T00:00:00Z',modes=['t'],production_go_granted=False))
        with self.assertRaisesRegex(ValueError,'production GO'):main(kit,'t')
        (cache/'a').symlink_to(kit/'k/a.json')
        self.assertEqual(B.scan(kit)['status'],'CLEAN')
        (cache/'b').symlink_to(root/'m')
        with self.assertRaisesRegex(ValueError,'Forbidden'):B.scan(kit)

    def test_worker_script_and_module_restoration(self):
        from launch_r2 import worker
        with patch.object(sys,'argv',['w',str(directory()),'t','1']):
            with self.assertRaisesRegex(ValueError,'arm'):runpy.run_path(worker.__file__,run_name='__main__')
        # The final-kit test stages the current source before this check.
        kit=LANE/load(LANE/'out/B3_KITS.json')[0]['kit_path']
        with patch.dict(sys.modules,{'v':object()}):
            previous=sys.modules['v'];B.verify(kit);self.assertIs(sys.modules['v'],previous)
