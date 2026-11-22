export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; N=o/174369_SUPERSEDED.txt; test -e $N || printf "superseded by tree db42866fd9e8d0090276686527e8ebd8837ab2a9401609d81039b8784187f034 per ORCH RULING 2026-11-22T05:14Z; nothing removed\n" > $N; cat $N >&2
J=174369
export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X; cp j/$J.log o/$J/job.log 2>/dev/null; du -sk o/$J >&2; tar czf - -C o $J
