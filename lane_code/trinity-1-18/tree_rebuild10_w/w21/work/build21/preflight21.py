from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build21';p=L/'work/tree_r1/launch_r1/production_proof.py'
text=p.read_text();old="        # Produce and bind the witness before native prepare validates the init boundary."
assert old in text
base=B/'base/launch_r1/production_proof.py';base.parent.mkdir(parents=True,exist_ok=True)
if not base.exists():base.write_text(text)
text=text.replace(old,"        # Refuse missing component evidence before writing capacity-sized stores.\n        from student_pilot.r1_training import training_components\n        with scope(closure['paths']):\n            training_components(cfg['r1_training']['registry'], cfg)\n        result['steps'].append('training_components')\n"+old)
p.write_text(text)
