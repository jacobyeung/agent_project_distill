O=/project/community/jjyeung/okh7; TZ=UTC date +%TZ >&2; cd $O/x_ee227714 < /dev/null && ls >&2
L=""; for h in b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad aacc34e66919a7f275d1e05d4621af193f6b14e0e5920bb2e732752f939d0e13 34916a84e82e61e9c8cf9bafa6a7f78e0ab18b4f4986ee07e76df930aee6276a; do for d in x_ee227714/u x_22c714e1/u; do [ -f $O/$d/$h ] && echo "$d/$h" >&2 && L="$L $d/$h"; done; done
cd $O && tar czf - $L 2>/dev/null
