cd /scratch/jjyeung/orch_n30/n_review1i/fx/fakeX/o < /dev/null || exit 3
ls -la 990777_gate < /dev/null 1>&2
L=""; for f in v.json identity.txt WAITING_REVIEW.json e0.json e1.json e2.json e3.json c0.json c1.json c2.json c3.json c4.json s2.json h0.json; do [ -f 990777/live/$f ] && L="$L 990777/live/$f"; done
G=""; [ -d 990777_gate ] && G=990777_gate
[ -z "$L$G" ] || du -cb $L $G < /dev/null 2>&1 | tail -1 1>&2
if [ -n "$L$G" ]; then tar cf - $L $G < /dev/null | base64 -w0; fi
