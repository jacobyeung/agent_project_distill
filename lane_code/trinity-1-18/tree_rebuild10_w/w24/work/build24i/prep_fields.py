from pathlib import Path
import sys,json,copy,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24i'
sys.path[:0]=[str(L/'work/build24'),str(L/'out')]
import joblib as J
from prep_diff import differences
fields={}
def add(path,reason,source):fields[path]=dict(reason=reason,source=source)
def pin(path,reason,source):
 for leaf in ('path','sha256'):add(path+'.'+leaf,reason,source)
pin('s1_routing.selection','Refresh the identical selection with the current producer. Row selection must remain identical.','b/a.py:q -> b/i.py:refresh')
for stream in ('vqa','routing','pointing'):
 pin('streams.'+stream,'Native preparation rebuilds and filters the stream receipt.','student_pilot/s1_admission.py:prepare_phase')
add('preparation_output','Native preparation assigns its attempt directory.','student_pilot/s1_admission.py:prepare_phase')
pin('preparation','Native preparation, population and handover each write a receipt. h.py/rv.py copy it to bind the host/review pins without changing identity.','student_pilot/s1_admission.py:prepare_phase; student_pilot/r1_population.py:bind_prepared; launch_r1/production_proof.py:bind_handover; b/rv.py:sync_preparation')
pin('routing_vocabulary','Produce the opener witness for the authenticated donor.','launch_r1/production_proof.py:_run; launch_r1/p_opener_witness.py:produce')
pin('r1_training.direction_augmented','Bind the generated direction-twin augmentation.','student_pilot/r1_direction_twins.py:augment')
pin('r1_training.room_audit','Census and bind the augmented VQA room audit.','launch_r1/production_proof.py:_run')
for stream in ('pose','vqa','routing','pointing'):
 add('r1_training.store_hashes.'+stream,'Derive the actual prepared stream identity; pose is the ordered composite-store identity.','student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover; student_pilot/r1_training.py:target_identity')
add('r1_training.continuation_identity','Bind the prepared target configuration.','student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover')
add('r1_training.row_plan_sha256','Hash the final native population sampler binding.','student_pilot/r1_population.py:bind_prepared; launch_r1/production_proof.py:bind_handover')
pin('r1_training.handover_mapping','Write the authenticated donor-to-prepared-target mapping.','student_pilot/r1_handover.py:bind_target; launch_r1/production_proof.py:bind_handover')
for name in ('population','indices'):
 pin('r2_sampling.'+name,'Bind final admitted native reader offsets and cell counts.','student_pilot/r1_population.py:produce,bind_prepared')
for name in ('host_receipt','review'):
 pin('r1_training.'+name,'Pin a job-private snapshot for the exact prepared identity. identity() excludes this pin.','launch_r1/entry.py:frame_host,admit; b/h.py; b/rv.py:run')
value=dict(schema='build24i-prep-fields-v1',comparison='Decoded k/c.json after resolver/entry localisation, immediately before a.py q; compare the same job view.',fields=dict(sorted(fields.items())),unchanged=['streams.pose','r2_sampling.card','r2_sampling.schema','recipe','admission','authorization','code','output','world_size','init_artifact','remove_files','r2_identity'],scope='Exact leaf paths, no wildcard or subtree permission. This checker checks locations, not semantic correctness or admission.')
J.write(L/'out/PREP_FIELDS.json',value)
pre=J.load(L/'work/build24f/rehearsal/input.json');actual=J.load(L/'work/build24f/rehearsal/v.json')
paths=list(differences(pre,actual));outside=sorted(set(paths)-fields.keys())
assert outside==['admission.path','admission.sha256','authorization.path','authorization.sha256'],outside
# The retained rehearsal explicitly adds two fixture-only gates after h.py.
normalized=copy.deepcopy(actual)
for key in ('admission','authorization'):normalized.pop(key)
assert all(p in fields for p in differences(pre,normalized))
J.write(D/'fixture_pre.json',pre);J.write(D/'fixture_prepared.json',normalized)
mutation=copy.deepcopy(normalized);mutation['recipe']['learning_rate']*=2;J.write(D/'fixture_mutated.json',mutation)
checks=[]
for name,p,expected in [('raw retained rehearsal',L/'work/build24f/rehearsal/v.json',1),('preparation without fixture gates',D/'fixture_prepared.json',0),('learning-rate mutation',D/'fixture_mutated.json',1)]:
 r=subprocess.run([sys.executable,'-I','-s','-B',str(L/'out/prep_diff.py'),str(D/'fixture_pre.json'),str(p)],text=True,capture_output=True)
 assert r.returncode==expected,(name,r.stderr,r.stdout);checks.append(dict(case=name,returncode=r.returncode,diff=r.stdout.splitlines()))
J.write(D/'PREP_FIELDS_TESTS.json',dict(status='PASS',checks=checks,fixture_only_paths=outside,fixture_sources_untouched=True))
lines=['The allowlist names exact leaf paths that preparation may change after entry localisation. The checker rejects any other change; it does not validate the permitted values.','',
'`python out/prep_diff.py pre.json v.json` prints every changed path and exits 1 if any path is outside the allowlist.','',
'The production mode-q path calls refresh, production_proof, native preparation, population and handover. It does not call frame_host; h.py still requires a genuine matching host receipt. entry.frame_host localises u/ paths before preparation and sets routing from routing_base. Those localisation changes belong in the comparison input. N is MINIMAL, so routing_inputs remain absent.','',
'The explicit recipe is already canonical; preparation may not change it. The pose receipt, sampler card, removals, configuration code pin and launch output also remain fixed.','',
'The retained 24f input.json versus v.json comparison has four extra leaf paths: admission.path, admission.sha256, authorization.path and authorization.sha256. fixture_gates.py adds these fixture-only gates after preparation. The raw comparison correctly exits 1; a separate copy omitting those gates passes. The retained files were not edited. A learning-rate mutation also exits 1. See work/build24i/PREP_FIELDS_TESTS.json.','',
'| Field | Reason and code |','|---|---|']
lines += ['| `'+p+'` | '+r['reason']+' `'+r['source']+'` |' for p,r in sorted(fields.items())]
(L/'out/PREP_FIELDS.md').write_text('\n'.join(lines)+'\n')
print(len(fields),'exact preparation paths; retained fixture exceptions verified')
