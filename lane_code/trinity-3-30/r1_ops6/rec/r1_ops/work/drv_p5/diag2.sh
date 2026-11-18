export TZ=UTC
O=/project/community/jjyeung/okh7
for d in $O/x_3fdda0fb $O/x_69d2930d.f170956 $O/x_69d2930d; do echo "== $d"; stat -c '%a %U %y %n' $d/b $d/k 2>&1; ls -la --time-style=+%m-%dT%H:%M $d/b/__pycache__ 2>&1 | head -8; done
ls -d $O/x_* | head -40 | tr '\n' ' '; echo
for d in $(ls -d $O/x_* | head -40); do [[ -d $d/b/__pycache__ ]] && echo "PYC $d"; done
grep -l "a_17c4ffa4" $O/x_*/b/r.sh 2>/dev/null | head
