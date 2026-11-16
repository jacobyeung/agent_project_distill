P=/project/community/jjyeung/okh7/b7e31d84a90c62f5/170206
for t in a8598721c7ff9494c e99ce848d0e2649b6; do
  echo "=========== $t"
  for m in $(tar tzf $P/$t/result.tar.gz); do echo "--- $m"; tar xzOf $P/$t/result.tar.gz "$m"; echo; done
done
