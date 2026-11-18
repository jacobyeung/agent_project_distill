P=/project/community/jjyeung/e09e45fda45db
cat /project/community/jjyeung/okh7/ae71c903/e09e45fda45db00029c87/JOB.log; echo =====
cd /tmp && mkdir -p rr1x && cd rr1x && tar xzf $P/a/f/0.tgz && for f in FAILED.json logs/0.log logs/1.log metadata/*.json; do echo "== $f"; tail -c 2500 $f; echo; done
