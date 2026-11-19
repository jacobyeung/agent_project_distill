from pathlib import Path
p=Path('code/replay.py');s=p.read_text();s=s.replace("def winning_box():", "def winning_box(context=None):")
s=s.replace("path=local(cfg['module_path']);assert sha(path)==cfg['module_sha256']", """decision=read_json(cfg['decision_path']);assert sha(cfg['decision_path'])==cfg['decision_sha256']
 verdict=decision
 for key in cfg['pass_pointer'].split('/'):
  if key:verdict=verdict[int(key)] if isinstance(verdict,list) else verdict[key]
 if verdict!='PASS':return None
 path=local(cfg['module_path']);assert sha(path)==cfg['module_sha256']""")
s=s.replace("return getattr(module,cfg['callable'])", "return getattr(module,cfg['callable'])(context)")
s=s.replace("min_member_frames=min(map(len,members)),box_records=", "min_member_frames=min(map(len,[printed_frames(v,c['anchor_slots']) for v in members] if n==64 else members)),dense_min_member_frames=min(map(len,members)),box_records=")
p.write_text(s)
p=Path('code/evaluate.py');s=p.read_text().replace('rule=winning_box()',"rule=winning_box(dict(capture=c,cache=cache64,geometry=geo64,n_frames=64))");p.write_text(s)
# Store provenance for diagnostics whose definitions come from the existing label and raw-prompt code.
import json,hashlib
p=Path('inputs/CODE_SOURCES.json');d=json.loads(p.read_text())
for source in [Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/work/refit/build_tables.py'),Path('/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook/heads/selector/sl118/sl_tables.py')]:
 d['input_sha256'][str(source)]=hashlib.sha256(source.read_bytes()).hexdigest()
p.write_text(json.dumps(d,indent=2)+'\n')
