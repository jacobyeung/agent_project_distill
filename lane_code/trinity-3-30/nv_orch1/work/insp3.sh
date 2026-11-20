cd /project/community/jjyeung/okh7/7b422049 && ls -la . | head -30
for f in *.json; do echo "== $f"; head -c 1500 $f; echo; done 2>/dev/null | head -80
