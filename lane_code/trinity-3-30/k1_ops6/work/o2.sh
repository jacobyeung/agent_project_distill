export TZ=UTC
P=/project/community/jjyeung/okh7/b7e31d84a90c62f5/170206
for t in a8598721c7ff9494c e99ce848d0e2649b6; do
  echo "=========== $t"
  for f in EXIT.json JOB.log RETURN_RECEIPT.json; do echo "--- $f"; cat $P/$t/$f; echo; done
  echo "--- tar list"; tar tzvf $P/$t/result.tar.gz
done
echo "--- probe"; ls -la $P/a1a9be3423cf847ae8da0fda86c36e6e7; od -c $P/a1a9be3423cf847ae8da0fda86c36e6e7 | head -3
