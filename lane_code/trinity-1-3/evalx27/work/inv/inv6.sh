set +e
export TZ=UTC
R=/home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz
echo "==== staging log"; tar xzOf $R logs/launcher_staging.log | head -80
echo "==== chain log head"; tar xzOf $R logs/launcher_chain.log | head -40
echo "==== sacct -B"; sacct -B -j 169526 2>&1 | head -150
