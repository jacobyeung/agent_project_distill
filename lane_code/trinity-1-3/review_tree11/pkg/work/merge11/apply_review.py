from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/merge11'
p=T/'student_pilot/fixed_readout.py';s=p.read_text();s=s.replace("            raise ValueError('invalid own depth')","            from .carrier_c1_routing import RenderError\n            raise RenderError('invalid own depth')");p.write_text(s)
p=T/'student_pilot/carrier_c1_run.py';s=p.read_text()
old="    for _,p in full_ft.base_parameters(model):\n        p.data=p.data.to(torch.bfloat16)\n    full_ft.load_export(model,Path(pinned(artifact['full_weights'])).parent)\n    state=torch.load(pinned(artifact['heads']),map_location='cpu',weights_only=True)"
new="""    state=torch.load(pinned(artifact['heads']),map_location='cpu',weights_only=True)
    readout_keys = {k for k in model.auxiliary_heads.state_dict()
                    if k.startswith(('depth_readout.', 'heading.'))}
    missing_readout = readout_keys - set(state)
    if missing_readout:
        reason = ('LEGACY_READOUT_EXPORT_UNSUPPORTED' if 'readout_config' not in artifact
                  else 'ARTIFACT_READOUT_BUFFERS_MISSING')
        raise ValueError(reason + ': ' + ', '.join(sorted(missing_readout)))
    for _,p in full_ft.base_parameters(model):
        p.data=p.data.to(torch.bfloat16)
    full_ft.load_export(model,Path(pinned(artifact['full_weights'])).parent)"""
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
p=T/'student_pilot/carrier_c1_batch_decode.py';s=p.read_text()
needle="""                if row.finish is not None:
                    results[i] = row.record()"""
replacement="""                except ValueError as exc:
                    row.finish = 'refused'
                    results[i] = row.record()
                    results[i]['refusal'] = str(exc)
                    results[i]['errors'] += 1
                    continue
                if row.finish is not None:
                    results[i] = row.record()"""
assert s.count(needle)==1;s=s.replace(needle,replacement);p.write_text(s)
p=L/'work/build10/eat1/run.py';s=p.read_text();old="""        if mon:
            mon.close()
    if scope is not None""";new="""        if mon:
            mon.close()
        for path, module, role, _ in declared:
            if role == 'fixed_math':
                artifact._check_buffers(path, module)
    if scope is not None""";assert s.count(old)==1;p.write_text(s.replace(old,new))
p=T/'tests/test_batched_routed_decode.py';s=p.read_text()
a=s.index('        with self.assertRaisesRegex',s.index('    def test_call_limit_and_context_cut_inside_response'))
b=s.index('\n    def test_shuffle',a)
s=s[:a]+'''        out = D.generate(model, p, rows, logits_processor=[Script(s) for s in
            [[1], [40, 41, 49], [32, 32], [42, 1]]], max_calls=1)
        self.assertEqual([r['finish'] for r in out], ['eos', 'refused', 'refused', 'eos'])
        self.assertTrue(all('call budget exhausted' in out[i]['refusal'] for i in (1, 2)))
        model.config.text_config.max_position_embeddings = rows[-1]['input_ids'].shape[1] + 3
        out = D.generate(model, p, rows, logits_processor=[Script(s) for s in
            [[40, 41], [32], [42, 42, 42, 42, 42, 42, 42, 42, 42, 42], [40, 41]]])
        self.assertEqual([r['finish'] for r in out], ['refused', 'refused', 'context_exhaustion', 'refused'])
        self.assertTrue(all('response exceeds token budget' in out[i]['refusal'] for i in (0, 1, 3)))

    def test_bad_frame_refuses_only_its_row(self):
        model, p, batch = fixture()
        rows = varied(batch, 2)
        out = D.generate(model, p, rows, logits_processor=[Script([33]), Script([42, 1])])
        self.assertEqual([r['finish'] for r in out], ['refused', 'eos'])
        self.assertIn('bad_frame', out[0]['refusal'])
        self.assertEqual(out[0]['calls'], [])
        self.assertEqual(out[1], D.generate(model, p, rows[1], logits_processor=Script([42, 1])))
''' + s[b:]
s=s.replace("        with self.assertRaisesRegex(ValueError, 'impersonate'):\n            D.generate(model, p, [batch], logits_processor=[Script([43])])", "        refused = D.generate(model, p, [batch], logits_processor=[Script([43])])[0]\n        self.assertEqual(refused['finish'], 'refused')\n        self.assertIn('impersonate', refused['refusal'])")
p.write_text(s)
(B/'legacy9fix_source.py').write_bytes((L.parent/'w9f/work/tree_r1/student_pilot/carrier_c1_run.py').read_bytes())
(T/'tests/test_merge11.py').write_text((B/'test_merge11_draft.py').read_text().replace('D.Heads','D.HeadState'))
p=L/'work/build10/eat1/tests/test_eat1.py';s=p.read_text();needle='    def test_outside_constant_still_fails_a3(self):'
s=s.replace(needle,'''    def test_buffer_mutation_during_generate_fails_a1(self):
        from types import SimpleNamespace
        model, art = self.make()
        def generate(frames, question):
            model.math.scale.fill_(7.)
            return dict(text='7', answer='7', calls=[])
        reader = SimpleNamespace(model=model, generate=generate)
        records, lines, declared = R.observe(reader, [dict(frames='fixture', question='fixture')], art,
            trace_lines=False, audit=False, monitor=False)
        self.assertIsNone(records[0]['error'])
        self.assertEqual(R.judge_a1(records, art, [])['status'], 'FAIL')
        self.assertEqual(art.buffer_offenders[0]['kind'], 'fixed_math_buffer_mismatch')

''' + needle);p.write_text(s)
(B/'STATUS.md').write_text('# Build 11 status\n\nThe merge proofs are recorded. Review fixes M1, M2, L1 and L2 are implemented; dedicated tests and final qualification remain pending. GO=false.\n')
