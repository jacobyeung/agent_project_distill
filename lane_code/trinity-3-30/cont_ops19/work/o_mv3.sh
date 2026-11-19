export TZ=UTC; P=/project/community/jjyeung/okh7/ae71c903; A=/project/community/jjyeung/okh7/ae71c903_fetched
for t in a4525db2f6a afdfd5caac6 d00c03dcc685e0002a39d; do test -d $P/$t && ! test -e $A/$t && mv $P/$t $A/$t && echo "moved $t"; done
for d in $P/*/; do find $d -type f -printf "%s\n"; done | awk '{s+=$1} END {print "pool bytes", s}'
