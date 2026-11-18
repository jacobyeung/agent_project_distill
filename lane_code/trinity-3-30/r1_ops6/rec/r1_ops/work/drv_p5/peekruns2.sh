export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d
find $KH/runs -type f -printf '%TT %s %P\n' 2>/dev/null | sort | tail -40
ls -la $KH/o | grep 171377 | awk '{print $5,$8,$9}'
tail -5 $KH/o/171377.steps; tail -c 3000 $KH/o/171377.err
