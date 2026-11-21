T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26fix/tree; cd $T
grep -rn 'torch\.cuda\.\|torch\.backends\.cuda\|cuda\.init\|_lazy_init\|NVML' student_pilot/s1_admission.py student_pilot/carrier_c1_data.py student_pilot/rehearsal.py student_pilot/first_batch_progress.py student_pilot/s1_exclusions.py launch_r1/production_proof.py launch_r1/entry.py launch_r1/p_opener_witness.py student_pilot/r1_population.py student_pilot/r1_persisted.py student_pilot/r1_loader.py student_pilot/r1_handover.py student_pilot/r1_training.py student_pilot/r1_direction_twins.py student_pilot/r1_rooms.py 2>/dev/null | cut -c1-200 | head -40
echo ===c1run; grep -n 'torch\.cuda\.' student_pilot/carrier_c1_run.py | cut -c1-180 | head -30
echo ===2850; sed -n 2855,2870p student_pilot/carrier_c1_run.py | cut -c1-200
echo ===forward; sed -n 17,33p launch_r1/production_proof.py | cut -c1-200
grep -n 'def first_batch_check' student_pilot/carrier_c1_run.py
