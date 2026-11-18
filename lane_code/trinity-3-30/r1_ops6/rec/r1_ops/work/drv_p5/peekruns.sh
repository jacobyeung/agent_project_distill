export TZ=UTC
KH=/project/community/jjyeung/okh7/x_69d2930d
find $KH/runs $KH/arm -maxdepth 4 -type f -printf "%TT %s %P\n" 2>/dev/null | sort | tail -30
ls $KH/o | grep 171377
