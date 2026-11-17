export TZ=UTC; P=/project/community/jjyeung/okh7/ae71c903; A=/project/community/jjyeung/okh7/ae71c903_fetched
mkdir -p -m 700 $A
for t in a24ea1a1936 af35386aa3e ae470417b41; do test -d $P/$t && ! test -e $A/$t && mv $P/$t $A/$t && echo "moved $t"; done
ls $A; for d in $P/*/; do find $d -type f -printf "%s\n"; done | awk '{s+=$1} END {print "pool bytes", s}'
