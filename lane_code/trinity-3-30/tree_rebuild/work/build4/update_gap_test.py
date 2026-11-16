from pathlib import Path
L=Path(__file__).resolve().parents[2]
p=L/'work/tree_r1/tests/test_r2_build3_gaps.py'
s=p.read_text()
start=s.index('    def test_real_dense_limit_and_entry_inventory(self):')
end=s.index('    def test_worker_script_and_module_restoration(self):',start)
replacement='''    def test_real_dense_limit_and_entry_inventory(self):
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

'''
p.write_text(s[:start]+replacement+s[end:])
