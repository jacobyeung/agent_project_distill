set -e; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X/q
while read h f; do f=${f#\*}; if [ ! -e "$f" ]; then s=""; for c in $X/a24/q_23d/$f $X/a24/over_q/$f; do [ -e "$c" ] && [ "$(sha256sum $c | cut -c1-64)" = "$h" ] && { s=$c; break; }; done; if [ -n "$s" ]; then mkdir -p $(dirname $f); cp -p $s $f; else echo "MISSING $f"; fi; fi; done < SHA256SUMS.txt
echo "q seal $(sha256sum SHA256SUMS.txt | cut -c1-16) bad $(sha256sum -c SHA256SUMS.txt 2>&1 | grep -vc ': OK$') files $(find . -type f | wc -l) lines $(wc -l < SHA256SUMS.txt) pyc $(find . -name __pycache__ | wc -l)"
sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ": OK$" | head -5
