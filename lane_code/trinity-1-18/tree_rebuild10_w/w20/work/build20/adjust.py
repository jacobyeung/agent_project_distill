from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/'work/tree_r1';B=L/'work/build20'
p=T/'tests/test_r1_build19.py';s=p.read_text()
s=s.replace("C.guard(dict(component_evidence={'init_m544':dict(status='VERIFIED')}),['VSI-Bench'],'reader')", "with self.assertRaisesRegex(ValueError,'COMPONENT_EVIDENCE_SLOTS_DIFFER'):\n            C.guard(dict(component_evidence={'init_m544':dict(status='VERIFIED')}),['VSI-Bench'],'reader')")
s=s.replace("identity=self.cfg['r2_identity']['init'])", "identity=dict(self.cfg['r2_identity']['init'],artifact_sha256=pin['sha256']))")
s=s.replace("cfg=bind_target(cfg,self.root/'mapping.json')", "cfg=bind_target(cfg,self.root/'mapping.json')\n        cfg['preparation']=write(self.root/'prepared.json',dict(schema='c1-preparation-v1',component_evidence=self.records(),r1_training=cfg['r1_training']))")
p.write_text(s)
# Native inputs preserve their authenticated content and path pins.
(B/'inputs').mkdir(exist_ok=True)
for name in ('config.json','kit_config.json','component_rows.json','mix.json'):
    (B/'inputs'/name).write_bytes((L/'work/build19/inputs'/name).read_bytes())
text=(L/'work/build19/native19.py').read_text().replace("B=L/'work/build19'", "B=L/'work/build20'")
# Use existing native rows to measure the storage budget before multiplying them.
(B/'native20.py').write_text(text)
text=(L/'work/build19/real19.py').read_text().replace("B=L/'work/build19'", "B=L/'work/build20'")
(B/'real20.py').write_text(text)
