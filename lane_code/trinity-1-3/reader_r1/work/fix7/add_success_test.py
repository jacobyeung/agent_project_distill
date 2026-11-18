from pathlib import Path
p=Path('bundle_regression.py');s=p.read_text();pos=s.index('    def test_payload_changes_only_token')
s=s[:pos]+'''    def test_cpu_helper_publishes_bound_guard_flag(self):
        root=fresh();results=root/'results';events=[]
        S,J,*_=common.template()
        cfg=common.read_config(O/'package');logical=cfg['logical']
        def stage(*args):
            events.append('stage');(root/'a').mkdir()
        def checked(argv,**kwargs):
            value=json.loads(Path(argv[-1]).read_text())
            if value.get('action')==0:
                events.append('prepare')
                settings=dict(stage1_select_rule='null_argmax',perception_memo='on' if O.name=='b2' else 'off',
                    perception_memo_modules=['g3t'],perception_memo_verify_ids=[],types=['room_size_estimation'])
                common.write(J.physical(root,logical+'/d/READY.json'),{'fixture':True})
                common.write(J.physical(root,logical+'/d/settings.json'),settings)
            else:
                events.append('sequence')
                common.write(J.physical(root,logical+'/r/metadata/MEMORY.json'),
                    dict(fits=True,basis='fixed_g3t_shapes',perception_memo_modules=['g3t'],sam_measurement_required=False))
                if O.name=='b2':
                    full=json.loads((O/'LOCAL_CPU_CHECK.json').read_text())['full_reader']
                    common.write(J.physical(root,logical+'/r/REHEARSAL.json'),[dict(full_reader=full)])
        with patch.object(node_check.tempfile,'mkdtemp',return_value=str(root)), \\
             patch.dict(os.environ,SLURM_JOB_ID='123'), \\
             patch.object(sys,'argv',['5.py','--package',str(O/'package'),'--sequence',str(O/'package/a/6.py'),'--results',str(results)]), \\
             patch.object(subprocess,'Popen',subprocess.Popen),patch.object(sys,'path',sys.path.copy()), \\
             patch.object(J,'storage_proof',return_value={'fixture':True}), \\
             patch.object(J,'namespace',return_value=[]),patch.object(J,'environment',return_value={}), \\
             patch.object(job,'stage',side_effect=stage),patch.object(common,'checked_run',side_effect=checked):
            node_check.main()
        proof=json.loads((results/'CPU.json').read_text())
        self.assertEqual(events,['stage','prepare','sequence'])
        self.assertIs(proof['passed'],True);self.assertIs(proof['bundle_guard_passed'],True)
        self.assertIs(proof['bundle_guard']['passed'],True)
        self.assertEqual(proof['bundle_guard']['operator_sha256'],sha(O/'package/a/6.py'))
        if O.name=='b2':self.assertIs(proof['full_reader_passed'],True)
        self.record('receipt',dict(passed=True,scope='Real bundle guard; staging, preparation and sequence outputs are fixtures',
                                  cpu=str(results/'CPU.json')))

''' +s[pos:];p.write_text(s)
