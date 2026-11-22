export TZ=UTC; date -u +%TZ
J=/project/community/jjyeung/okh7/x_ee227714
ls -la $J | head -40
for d in ck x x/ck o s s/c7d31ddd s/c7d31ddd/venvs; do [ -d $J/$d ] && { echo "== $d"; ls -la $J/$d | head -20; }; done
echo "== c7d"; ls -la /project/community/jjyeung/c7d31ddd /project/community/jjyeung/c7d31ddd/* 2>&1 | head -20
grep -n "slot A\|checkpoint 600" $J/o/172660.steps 2>/dev/null | head -5
