S=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w26trace/s
grep -rn --include=*.py 'donor_meta_model\|def bind_target\|def donor\b\|def donor(' $S/student_pilot $S/launch_r1 | head -20
grep -n 'def is_flash_linear_attention_available' -A6 /scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages/transformers/utils/import_utils.py
