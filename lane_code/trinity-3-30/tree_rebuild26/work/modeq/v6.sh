T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26fix/tree; cd $T
echo "== module-level imports"; for f in student_pilot/s1_admission.py student_pilot/carrier_c1_run.py student_pilot/carrier_c1_data.py student_pilot/rehearsal.py student_pilot/first_batch_progress.py student_pilot/s1_exclusions.py; do echo "-- $f"; grep -n '^import \|^from ' $f | cut -c1-160 | head -25; done
echo "== fla/triton/transformers/flash anywhere (with indent)"; grep -rn 'import fla\|from fla\|import triton\|from triton\|import transformers\|from transformers\|flash_attn\|flash_linear' student_pilot launch_r1 | cut -c1-170 | head -30
echo "== s1_admission calls into run/data"; grep -n 'run\.\|data\.\|rehearsal\.' student_pilot/s1_admission.py | cut -c1-170 | head -40
