from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1'
p=T/'tests/coverage_b8_preparation.py';s=p.read_text()
a=s.index('            try:\n                trainer.prepare(cfg)')
b=s.index("            cfg['h1']={'faithful_own_camera_rows':False}",a)
s=s[:a]+'''            faithful_receipt=trainer.prepare(cfg)
            self.assertTrue(faithful_receipt['h1_faithful_identity']['passes'])
'''+s[b:]
s=s.replace('return cfg,prepared,faithful_refusal','return cfg,prepared,faithful_receipt')
p.write_text(s)
p=T/'tests/test_r2_build8.py';s=p.read_text().replace('faithful_refusal','faithful_receipt')
s=s.replace("self.assertFalse(faithful_receipt['h1_faithful_identity']['passes'])","self.assertTrue(faithful_receipt['h1_faithful_identity']['passes'])")
s=s.replace('dict(identity_refusal=faithful_receipt','dict(identity=faithful_receipt')
p.write_text(s)
