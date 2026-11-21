T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26fix/tree; cd $T
for f in student_pilot/carrier_c1.py student_pilot/full_ft.py student_pilot/decoupled_v_run.py student_pilot/r1_training.py student_pilot/carrier_c1_sweep.py; do echo "-- $f"; grep -n '^import \|^from \|^    from transformers\|^    import transformers' $f | grep -v '^[0-9]*:from \.\(p3_provenance\|job_env\) ' | cut -c1-150 | head -14; done
echo "== s1_admission prepare_only"; grep -n 'prepare_only' student_pilot/s1_admission.py | head; sed -n 222,256p student_pilot/s1_admission.py | cut -c1-170
echo "== production_proof before admit: imports in _run"; sed -n 64,136p launch_r1/production_proof.py | grep -n 'import\|training_components\|opener\|augment' | cut -c1-170
