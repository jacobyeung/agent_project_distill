from pathlib import Path
p=Path('code/replay.py');s=p.read_text().replace("r=cache['frames'][str(i)]['phrases'][key];presence=float(r['presence'])\n  chosen=[p for p in sorted(r.get('instances') or [],key=lambda p:-float(p['score'])) if float(p['score'])*presence>=.05][:30]", """r=cache['frames'][str(i)]['phrases'][key]
  raw=[p for p in r.get('instances') or [] if p.get('source_prompt',key)==key]
  presence=float(raw[0]['source_presence']) if raw and 'source_presence' in raw[0] else float(r['presence'])
  if raw and len({p.get('source_presence') for p in raw})!=1:raise ValueError('Raw-name source presence differs')
  chosen=[p for p in sorted(raw,key=lambda p:-float(p['score'])) if float(p['score'])*presence>=.05][:30]""")
p.write_text(s)
p=Path('code/test_kit.py');s=p.read_text();needle=' def test_direction_uses_reader(self):';s=s.replace(needle,''' def test_raw_name_filter(self):
  from replay import cached_detections
  cache=dict(phrases=['chairs'],frames={'0':dict(phrases={'chairs':dict(presence=1.,instances=[dict(score=.99,source_prompt='chair',source_presence=1.,mask=dict(size=[1,1],counts=[0,1])),dict(score=.8,source_prompt='chairs',source_presence=.5,mask=dict(size=[1,1],counts=[0,1]))])})})
  got=cached_detections(cache,'chairs',1);self.assertEqual(len(got[0]),1);self.assertEqual(got[0][0]['presence'],.5)
''' +needle)
p.write_text(s)
