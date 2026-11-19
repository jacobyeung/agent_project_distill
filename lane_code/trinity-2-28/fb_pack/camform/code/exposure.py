"""Derive conditional form exposure from authenticated code; do not invent an N card."""
from pathlib import Path
import json,hashlib,sys
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[1];TREE=ROOT/'work/new';sys.path.insert(0,str(TREE))
from student_pilot.r1_training import STREAMS
from student_pilot.r2_mix import table,allocation
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'out/SOURCE_TESTS.json';tests=json.loads(source.read_text())
config=ROOT.parent/'ro/orch_n30/tree_rebuild10_w/w24/work/build24f/launch_tests/config.json'
cfg=json.loads(config.read_text());card=cfg['r1_training']['mix'];expected=config.parent/card['path']
inputs={str(p):sha(p) for p in [Path(__file__),source,config,TREE/'student_pilot/r1_training.py',TREE/'student_pilot/r1_coverage.py',TREE/'student_pilot/r1_mix.py',TREE/'student_pilot/r2_mix.py']}
assert not expected.exists(), 'Inspect available card rather than treating it as missing'
nominal=table();cells={c['type']:Fraction(c['numerator'],c['denominator']) for c in nominal['cells']}
rot=cells['camera_rotation'];direction=cells['camera_movement_direction'];affected=Fraction(tests['rewritten_by_type']['camera_movement_direction'],tests['types']['camera_movement_direction'])
records=[]
for name,before,after in [('rotation_numeric_convention',rot,0),('rotation_word_convention',0,rot),('direction_numeric_negation',direction*affected,0),('direction_symbolic_negation',0,direction*affected),('direction_no_negative_option',direction*(1-affected),direction*(1-affected))]:
 records.append(dict(form=name,field_absent=str(before),field_enabled=str(after),field_absent_decimal=float(before),field_enabled_decimal=float(after)))
value=dict(input_sha256=inputs,command='nice -n 10 env OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 /scratch/jjyeung/envs/p1cpu/bin/python -B code/exposure.py',routing_rows_per_step=STREAMS['routing'],source_camera_rows=6000,observed_rewrites=3996,conditional_expected_rewritten_camera_rows='C * (2000/6000 + 1996/6000) = 0.666*C',conditional_expected_by_type='B_rotation + 0.998*B_direction',C='Number of eligible base camera rows; MISSING full routing base census',N_actual_per_step='MISSING',N_base_form_draws=dict(rotation_numeric_without_field='r_rotation',rotation_numeric_with_field='0',rotation_words_without_field='0',rotation_words_with_field='r_rotation',direction_numeric_without_field='0.998*r_direction',direction_numeric_with_field='0',direction_symbolic_without_field='0',direction_symbolic_with_field='0.998*r_direction',direction_no_negation_both='0.002*r_direction'),N_formula_scope='r_rotation/r_direction are admitted base-row draws per step, excluding already rewritten camera_wording slices. The full card, filtered cell counts and source shares are required to assign numbers; this extract is camera-only.',missing=[dict(name='N pinned mix/card and filtered base camera census',expected_location="cfg['r1_training']['mix'], cfg['r2_sampling']['population'], cfg['streams']['routing'] and its database",status='MISSING'),dict(name='Card referenced by available launch-test config (not proof of production N binding)',expected_location=str(expected),original_relative_path=card['path'],expected_sha256=card['sha256'],status='MISSING')],tree_nominal_r2_table_conditional=dict(scope='r2_mix.table() plan only, not an authenticated N card. Assumes no allocation caps, all rotation/direction draws come from base, and extract match rates transfer. Do not report as actual N exposure.',camera_rotation_rows_per_step=str(rot),camera_direction_rows_per_step=str(direction),forms=records))
for name,pin in [('Filtered population referenced by available launch-test config',cfg['r2_sampling']['population']),('Routing receipt referenced by available launch-test config',cfg['streams']['routing'])]:
 expected_path=config.parent/pin['path']
 if not expected_path.exists():
  value['missing'].append(dict(name=name,expected_location=str(expected_path),original_relative_path=pin['path'],expected_sha256=pin['sha256'],status='MISSING'))
(ROOT/'out/EXPOSURE.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k not in ('input_sha256','N_base_form_draws')},indent=2))
