export TZ=UTC; date -u +%TZ
sacct -j 174353,174354 -X -n -P -o JobID,State,NodeList,Elapsed
for f in ~/a15o/orchard-community-3.out ~/a15o/orchard-community-2.out; do echo "== $f"; cat $f 2>&1 | cut -c1-200 | head -40; done
