from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9'
s=(L/'work/tree_r1/tests/test_r2_build9_cpu.py').read_text()
s=s.replace('from student_pilot.carrier_c1 import CarrierC1','from student_pilot.carrier_c1 import CarrierC1\n        from student_pilot.carrier_c1_sweep import recipe_for')
s=s.replace("frame_layout='duplicate',frame_count=32)","frame_layout='duplicate',frame_count=32,recipe=recipe_for({'training_mode':'final'}))")
s=s.replace("self.assertTrue(torch.isfinite(result['loss']))","self.assertTrue(torch.isfinite(result['loss']))\n        self.assertGreater(float(result['loss']),0.)\n        self.assertGreater(float(result['components']['routing']),0.)")
s=s.replace("loss=float(result['loss']),","loss=float(result['loss']),routing_loss=float(result['components']['routing']),supervised_tokens=int((batch['labels']!=-100).sum()),")
(B/'weighted_cpu.py').write_text(s)
