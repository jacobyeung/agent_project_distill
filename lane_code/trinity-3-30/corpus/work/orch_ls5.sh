cd /project/community/jjyeung/okh7 || exit 1
for d in x_69d2930d x_ee227714 x_07ca49df; do echo "== $d"; ls $d; ls $d/o | head -30; done
find x_69d2930d x_ee227714 -maxdepth 4 -iname "*metric*" -printf "%s %p\n" | head -20
