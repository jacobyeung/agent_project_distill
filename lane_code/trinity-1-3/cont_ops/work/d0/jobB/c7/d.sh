export TZ=UTC; KB=/project/community/jjyeung/okh7/x_f5c353f7
date -u +%T; ls -la --time-style=+%T $KB/o/ | grep 'gcs_359fcc3c_m.*\.done' | tail -2; tail -2 $KB/o/170111.steps; squeue -h -u jjyeung -o '%i %j %P %T %M %r'
