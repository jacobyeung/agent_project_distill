P=/project/community/jjyeung/a3b73b53d92a7/a
ls -la $P/c | head -20; cat $P/18; echo; cat $P/21; echo
for f in $P/c/*.json; do echo "== $f $(stat -c %s $f)"; head -c 1500 $f; echo; done 2>&1 | head -c 6000
