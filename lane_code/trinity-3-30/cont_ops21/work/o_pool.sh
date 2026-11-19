cd /project/community/jjyeung/okh7
for d in ae71c903/*; do n=$(basename $d); for L in 13 11; do t=${n:0:$L}; P=a15_cot_ap$t; [ -d $P ] && break; done
 j=${n:${#t}}; jd=$([ -n "$j" ] && printf '%d' 0x$j); echo "$n tok=$t job=$jd pkg=$([ -d $P ] && echo y || echo n) 8txt=$(cat $P/a/8.txt 2>/dev/null) f=$(ls $P/a/f 2>/dev/null | tr '\n' ,) mtime=$(stat -c %y $d | cut -c1-16) files=$(ls $d | tr '\n' ,)"; done
ls ae71c903_fetched | tail -5
