from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
s=(L/'work/tree_r1/tests/test_r2_build9_cpu.py').read_text()
s=s.replace('from student_pilot.carrier_c1 import CarrierC1','from student_pilot.carrier_c1 import CarrierC1\n        from student_pilot.carrier_c1_sweep import recipe_for')
s=s.replace("root=D.directory();row=ground(root,'recovery')",'''root=D.directory();row=ground(root,'recovery')
        from trace_format.ground_v313 import Session
        from student_pilot.ground_rows import pack
        # Empty provider output is the explicit simulated failure input.
        session=Session(None,None,None,instances=lambda name:[],program_version='3.14')
        record=deepcopy(row['ground_record']);call=record['events'][0]['call']
        self.assertEqual(session.execute(call),'ceiling lamp: not seen')
        event=session.events[0];event['audit'].update(simulated=True,status='not seen')
        record['suffix']=row['target'].replace(record['events'][0]['response'],event['response'])
        record['events']=[event]
        row.update(pack(record,row['provenance']))''')
s=s.replace("frame_layout='duplicate',frame_count=32)","frame_layout='duplicate',frame_count=32,recipe=recipe_for({'training_mode':'final'}))")
s=s.replace("self.assertTrue(torch.isfinite(result['loss']))","self.assertTrue(torch.isfinite(result['loss']))\n        self.assertGreater(float(result['loss']),0.)\n        self.assertGreater(float(result['components']['routing']),0.)")
s=s.replace("loss=float(result['loss']),","loss=float(result['loss']),routing_loss=float(result['components']['routing']),supervised_tokens=int((batch['labels']!=-100).sum()),")
s=s.replace("real_functions=['r2_materialize.materialize'","real_functions=['ground_v313.Session.execute','box_v313.ground','ground_rows.pack','r2_materialize.materialize'")
s=s.replace('Synthetic RGB and a synthetic printed failure event; no real-frame or deployment claim.','Synthetic RGB and an empty instance-provider result. The native formatter produces the failure event; no real-frame or deployment claim.')
(B/'weighted_cpu.py').write_text(s)
