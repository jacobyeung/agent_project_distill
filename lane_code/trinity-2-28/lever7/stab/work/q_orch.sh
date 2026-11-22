P=/project/community/jjyeung
echo "== pool"; ls $P/okh7/ae71c903/ 2>&1 | grep -E '^b01ec87a6f29b|^b9ef552934627' | head -20
for d in $P/okh7/ae71c903/b01ec87a6f29b00029a87 $P/okh7/ae71c903/b9ef55293462700029cf5 $P/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2; do echo "== $d"; ls -la $d 2>&1 | head -20; done
for d in $P/okh7/ae71c903/b01ec87a6f29b*; do [ -f $d/result.tar.gz ] && echo "$d $(sha256sum < $d/result.tar.gz | cut -c1-64) $(stat -c %s $d/result.tar.gz)"; done
f=$P/okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/items.jsonl; [ -f $f ] && sha256sum $f && wc -l < $f
for d in $P/okit/evalx_results $HOME/okit/evalx_results; do echo "== $d"; ls -la $d 2>&1 | head -30; done
for d in $P/okit/evalx_results/*e193c2a3c* $HOME/okit/evalx_results/*e193c2a3c*; do [ -e "$d" ] && ls -la "$d" && [ -f "$d/result.tar.gz" ] && sha256sum "$d/result.tar.gz"; done 2>/dev/null
