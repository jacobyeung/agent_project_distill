cd /project/community/jjyeung/okh7/x_22c714e1/o < /dev/null || exit 3
ls -la 174083_gate < /dev/null 1>&2
L=""; for f in v.json identity.txt WAITING_REVIEW.json e0.json e1.json e2.json e3.json c0.json c1.json c2.json c3.json c4.json s2.json h0.json; do [ -f 174083/live/$f ] && L="$L 174083/live/$f"; done
G=""; [ -d 174083_gate ] && G=174083_gate
[ -z "$L$G" ] || du -cb $L $G < /dev/null 2>&1 | tail -1 1>&2
if [ -n "$L$G" ]; then tar cf - $L $G < /dev/null | base64 -w0; fi
