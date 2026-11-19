K=/project/community/jjyeung/okh7/x_ee227714; cd $K; ls | head -30; echo ==; ls runs/6ed2c7aa | head; echo ==
grep -rIl --include='*.py' -e 'pose_lr_scale' . 2>/dev/null | head -20; echo ==
grep -rIn --include='*.py' -E 'scale_head|ScaleHead|metric_scale|log_scale|scale_token' . 2>/dev/null | head -40
