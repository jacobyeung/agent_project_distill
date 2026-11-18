export TZ=UTC; P=/project/community/jjyeung/okh7/ae71c903; A=/project/community/jjyeung/okh7/ae71c903_fetched
t=a5f07824bb3; test -d $P/$t && ! test -e $A/$t && mv $P/$t $A/$t && echo "moved $t"
ls $A; for d in $P/*/; do find $d -type f -printf "%s\n"; done | awk '{s+=$1} END {print "pool bytes", s}'
