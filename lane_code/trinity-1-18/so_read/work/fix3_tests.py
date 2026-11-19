from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read');E=L/'work/src/u0'
p=E/'tests/test_read_cache.py';s=p.read_text().replace('restore, snapshot, switches)','restore, snapshot, switches, ModelMutationError)')
s=s.replace('''            visual.weight.add_(1)
            visual(torch.ones(2),torch.tensor([1,1,2]));self.assertEqual(visual.calls,2)
            visual.weight.data.fill_(9.)
            result=visual(torch.ones(2),torch.tensor([1,1,2]));self.assertEqual(visual.calls,3)
            self.assertEqual(float(result.pooler_output),18.)
        with self.assertRaisesRegex(ValueError,'no-grad'): visual(torch.ones(2),torch.tensor([1,1,2]))''','''        with self.assertRaisesRegex(ValueError,'no-grad'): visual(torch.ones(2),torch.tensor([1,1,2]))
        with torch.no_grad():
            visual.weight.add_(1)
            with self.assertRaises(ModelMutationError):visual(torch.ones(2),torch.tensor([1,1,2]))
        self.assertEqual(visual.calls,1)''')
a=s.index('            tower._backend.model.weight=torch.nn.Parameter')
b=s.index("            handle=tower._backend.model.register_forward_pre_hook",a)
s=s[:a]+s[b:]
s=s.replace("{'encode':7,'detect':8}","{'encode':5,'detect':6}").replace("{'encode':9,'detect':10}","{'encode':7,'detect':8}").replace("{'encode':10,'detect':12}","{'encode':8,'detect':10}")
s=s.replace("            self.assertEqual(calls,{'encode':8,'detect':10})","""            self.assertEqual(calls,{'encode':8,'detect':10})
            tower._backend.model.weight=torch.nn.Parameter(torch.tensor([[9.]]),requires_grad=False)
            with self.assertRaises(ModelMutationError):factory(frames,'mutated').propose('chair')""")
s=s.replace("for module,enabled in ((original,False),(patched_off,False),(parity,True)):","for module,enabled in ((original,False),(patched_off,False),(parity,True),(parity,'processor')):")
s=s.replace("            if enabled:cfg.update(read_processor_cache='on',read_vision_cache='on')","            if enabled:cfg.update(read_processor_cache='on',read_vision_cache='on')\n            if enabled=='processor':cfg['read_processor_only']='on'")
s=s.replace('                values=[gen(t) for t in tasks]','''                if enabled=='processor':self.assertFalse(hasattr(gen,'weight_boundary'))
                values=[gen(t) for t in tasks]
                if enabled=='processor':
                    self.assertEqual(values[-1]['read_cache']['enabled'],['read_processor_cache'])
                    self.assertEqual(values[-1]['read_cache']['stats']['processor']['hits'],45)
                if enabled is True:gen.weight_boundary()''')
s=s.replace('        self.assertEqual(hit_counts,[50,50,5])','        self.assertEqual(all_results[0],all_results[3])\n        self.assertEqual(hit_counts,[50,50,5,50])')
p.write_text(s)
p=E/'tests/test_round1.py';p.write_text(p.read_text().replace('except ValueError:return',"except (ValueError,getattr(C,'ModelMutationError',ValueError)):return"))
# Keep the environment regression behavioral; select the vulnerable F16 baseline explicitly.
p=E/'tests/test_round3.py';s=p.read_text();s=s.replace("        kit=load('round3_kit_worker',KIT/'run.py');root=directory()", "        path=L/'work/round2-before/kit/run.py' if os.environ.get('READ_F16_BEFORE')=='1' else KIT/'run.py'\n        kit=load('round3_kit_worker',path);root=directory()")
s=s.replace("            with patch.dict(os.environ,{'CUDA_VISIBLE_DEVICES':'fixture'},clear=False), \\","            with patch.object(kit,'os',types.SimpleNamespace(environ={'CUDA_VISIBLE_DEVICES':'fixture'})), \\")
s=s.replace("                os.environ.pop('H10_SETTINGS',None)\n",'')
s=s.replace("                self.assertNotIn('H10_SETTINGS',os.environ)","                self.assertNotIn('H10_SETTINGS',kit.os.environ)")
pos=s.index('    def test_f3_both_base_')
s=s[:pos]+'''    def test_f1_type_boundary_failure_blocks_resume_and_merge(self):
        self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing weight boundary')
        fixtures=load('round3_journal_fixture',SRC/'u0/tests/test_read_journal.py')
        if BEFORE:fixtures.launch=load('h1eval.h10.launch',E/'a4.py')
        case=fixtures.RunnerTests();case.setUp()
        try:
            m,store=visual();calls=[];hashes=[]
            original=C.weight_digest
            def hashed(model):hashes.append(True);return original(model)
            args=case.args('checked');args.types='camera_rotation'
            def factory(*a,**kw):
                def generate(item):
                    calls.append(item['id'])
                    with torch.no_grad():m(torch.ones(1,32))
                    if item['id']=='4':m.weight.data.add_(1)
                    return fixtures.row(item['id'])['output']
                generate.weight_boundary=store.weight_boundary
                return generate
            with patch.object(C,'weight_digest',side_effect=hashed):
                with self.assertRaises(C.ModelMutationError):fixtures.launch.run_types(args,make_real=factory)
            self.assertEqual(calls,['0','1','2','3','4'])
            self.assertEqual(len(hashes),2) # type entry and exit; none per item
            root=Path(args.out)/'1/0'
            from orchard_h10.common import ORDER
            root=Path(args.out)/str(ORDER.index('camera_rotation'))/'0'
            self.assertFalse(json.loads((root/'WEIGHTS.json').read_text())['verified'])
            with self.assertRaisesRegex(ValueError,'Unchecked cache weights'):
                fixtures.launch.run_types(args,make_real=factory)
            with self.assertRaisesRegex(ValueError,'Unchecked cache weights'):
                fixtures.merge(case.manifest,[root],case.root/'bad-merge')
        finally:case.doCleanups()

'''+s[pos:];p.write_text(s)
