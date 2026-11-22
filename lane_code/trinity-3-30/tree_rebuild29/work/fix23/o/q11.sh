export TZ=UTC; date -u +%TZ; sacct -j 174381 -X -n -P -o State,NodeList; cat ~/a15o/f23/l3.out | grep -v error:
