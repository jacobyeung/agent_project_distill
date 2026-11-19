T=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w23/work/tree_r1; cd $T
grep -rn "freeze\|frozen\|requires_grad_(\|requires_grad *=\|trainable\|no_decay\|param_groups\|lr_mult\|lr_scale" --include=*.py student_pilot launch_r1 launch_r2 2>/dev/null | grep -v "/tests/" | cut -c1-200 | head -40
echo; grep -rln "pose_scale\|scale_head\|log_scale\|metric_scale\|tower" --include=*.py student_pilot launch_r1 2>/dev/null | grep -v tests | head -12
