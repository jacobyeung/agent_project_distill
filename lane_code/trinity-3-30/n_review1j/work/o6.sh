O=/project/community/jjyeung/okh7; TZ=UTC date +%TZ >&2; L=""
for d in x_22c714e1/u x_ee227714/u; do for h in $(cd $O/$d < /dev/null && ls 2>/dev/null | grep -E '^(ddff748d|aaecc9c4|8091154c|dc03d271|a7682dae)'); do echo "$d/$h" >&2; L="$L $d/$h"; done; done
cd $O && tar czf - $L 2>/dev/null
