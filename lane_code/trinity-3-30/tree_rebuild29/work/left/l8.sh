export TZ=UTC; date -u +%TZ; sacct -j 174357 -X -n -P -o State,Elapsed; cat ~/a15o/d3.out | cut -c1-160 | head -50
