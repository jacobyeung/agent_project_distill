set +e
export TZ=UTC
R=/home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz
K=/project/community/jjyeung/okh7/r/5da50f2b
for f in A.json A.sha256 A.verify.part RUN.json binding.json; do echo "==== $f"; cat $K/$f; echo; done
echo "==== members not merged-kit"; tar tzvf $R | grep -v 'kit/evaluator/' | grep -v '/results/' | awk '{print $3, $6}' | sed -n 1,200p
echo "==== source.tar of merged/main"; tar xzOf $R merged/main/kit/source.tar | tar tvf - | head -80
echo "==== tar ebe307cf4 members"; tar tzf /home/jjyeung/okit/evalx_results/ebe307cf4/result.tar.gz | grep -v '/results/' | grep -v 'kit/evaluator/' | head -120
