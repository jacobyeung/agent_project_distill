J=174415
export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; cp j/$J.log o/$J/job.log 2>/dev/null; du -sk o/$J >&2; tar czf - -C o $J
