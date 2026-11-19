"""Seal the probe evidence and write the lane handoff without launching training."""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths2 import D,L,R
from rehearsal_inputs2 import usage,PLAN_LIMIT
sys.path.insert(0,str(L/'work/build24'))
import joblib as J

setup=J.load(R/'SETUP.json')
current_kit=J.seal(Path(setup['kit_dir']))
fixture_kit=J.seal(R/'kit_n_go')
assert J.sha(R/'kit_n_go'/setup['source']['path'])==setup['source']['sha256']
layout=J.load(R/'INPUT_LAYOUT.json')
assert all(J.sha(Path(item['path']))==h for h,item in layout['stores'].items())
assert not (D/'rehearsal_k2').exists()
assert not any((R/('train_'+p+'.log')).exists() for p in ('fresh','budget','resume'))
assert (R/'frame_audit_check/RESULT.json').is_file()
scripts=['rehearsal_inputs2.py','rehearsal_paths2.py','make_rehearsal_k2.py',
         'rehearsal_boundary2.py','rehearsal_runner2.py','check_rehearsal_inputs.py',
         'check_rehearsal_k3_finish.py','check_rehearsal.py']
for name in scripts:ast.parse((D/name).read_text(),filename=name)
subprocess.run(['bash','-n',str(D/'go_rehearsal_k.sh')],check=True)
subprocess.run([sys.executable,'-I','-s','-B',str(D/'check_rehearsal_inputs.py'),'--probe-result'],check=True)
result=subprocess.run([sys.executable,'-I','-s','-B',str(D/'check_rehearsal.py')],capture_output=True,text=True)
assert result.returncode==1
assert len(J.load(R/'CHECK.json'))==11
probe=J.load(R/'PROBE_RESULT.json')
validation=dict(status='PASS',probe_selected_kit_seal=setup['kit'],current_kit_seal=current_kit,
    selected_kit_changed_since_probe=current_kit!=setup['kit'],fixture_kit_seal_verified=fixture_kit,
    source_archive_sha256_verified=setup['source']['sha256'],fixture_database_hashes_unchanged=True,
    linked_store_checks=probe['linked_store_checks'],native_frame_audit='frame_audit_check/RESULT.json',
    code={name:J.sha(D/name) for name in scripts},guard_mutations='check_rehearsal_inputs.py',
    final_directory_absent=True,training_executed=False)
J.write(R/'VALIDATION.json',validation)
# Include evidence-file sizes in the final measurement, without counting the
# shared database inodes as new storage or counting repeated links twice.
for _ in range(3):
    probe.update(usage(R));probe['bytes_after_stop']=probe['new_bytes']
    J.write(R/'PROBE_RESULT.json',probe)
measured=usage(R)
assert measured['retained_allocated_bytes']<1_200_000_000
budgets=probe['budgets']
planned=[budgets[n]['planned_bytes'] for n in ('routing_retained','p2')]
assert max(planned)<PLAN_LIMIT
report=[
    'READY FOR FINAL-KIT REHEARSAL: the bounded native probe reaches exactly P_EXPORT_RUN_BINDING_MISMATCH in the tested kit.',
    'The harness stages only the rehearsal3 fixture closure, a single RGB image, and five hard-linked fixture databases; it excludes the inherited production upload catalog and request path map (rehearsal_k3_probe/INPUT_LAYOUT.json).',
    f'Native plans: routing {planned[0]:,} bytes; canary {planned[1]:,} bytes, both below the 600,000,000-byte pre-copy cap (rehearsal_k3_probe/routing_retained/STAGING_BUDGET.json and p2/STAGING_BUDGET.json).',
    f'The probe retained {measured["new_bytes"]:,} new file bytes and allocated {measured["allocated_bytes"]:,} new disk bytes; including linked inputs, unique retained allocation is {measured["retained_allocated_bytes"]:,} bytes, below 1.2 GB (rehearsal_k3_probe/PROBE_RESULT.json).',
    'Native routing exits 0; native q exits 1 after direction_twins and training_components with ValueError:P_EXPORT_RUN_BINDING_MISMATCH (rehearsal_k3_probe/STAGES.json and p2/q/RESULT.json).',
    f'The probe used verified kit {setup["kit"][:8]}; its preserved fixture kit and source archive verify. The concurrent kit build now seals as {current_kit[:8]}; no fallback or probe rerun occurred (rehearsal_k3_probe/SETUP.json and VALIDATION.json).',
    'The cap mutations, syntax, unchanged database hashes, both stages’ shared inodes, and a separate native RGB containment/hash/inventory audit pass (rehearsal_k3_probe/VALIDATION.json and frame_audit_check/RESULT.json).',
    'The fixture frame-host boundary maps only /data2/f.png into the staged frame root. This harness leaves native admission, handover checks, supplied kits, packages, tree and out/ unedited.',
    'The launcher retains native q/d.py/h.py/rv.py, the selected kit copier and the budget/resume v.json re-pin. All 11 downstream rows remain NOT PROVED; no four-rank training ran (rehearsal_k3_probe/CHECK.json).',
    'After the corrected tree is sealed into the final kit, run once into the absent rehearsal_k2 directory:',
    f'`cd {L} && REHEARSAL_K2_ROOT={D}/rehearsal_k2 REHEARSAL_K2_PROBE=0 nice -n 10 bash work/build24k/go_rehearsal_k.sh out/kit_n_go`',
]
assert len(report)<15
(D/'REHEARSAL_K2_REPORT.md').write_text('\n'.join(report)+'\n')
print(json.dumps(dict(status='PASS',planned_bytes=planned,**measured,report=str(D/'REHEARSAL_K2_REPORT.md')),indent=2))
