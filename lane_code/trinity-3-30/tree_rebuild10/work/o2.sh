K=/project/community/jjyeung/okh7/x_69d2930d/k; cd $K && ls -la benchmark_scene_exclusions.json 66c427e2.json remove_1.jsonl remove_2.jsonl remove_3.jsonl 2>&1; sha256sum benchmark_scene_exclusions.json 66c427e2.json remove_1.jsonl remove_2.jsonl remove_3.jsonl 2>&1 | cut -c1-16,65-
S=$(du -cb benchmark_scene_exclusions.json 66c427e2.json remove_1.jsonl remove_2.jsonl remove_3.jsonl 2>/dev/null | tail -1 | cut -f1); echo TOTAL=$S
if [ "${S:-0}" -lt 20000000 ]; then echo B64BEGIN; tar czf - benchmark_scene_exclusions.json 66c427e2.json remove_1.jsonl remove_2.jsonl remove_3.jsonl | base64 -w0; echo; echo B64END; fi
P=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa; ls -la $P/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820 $P/inputs/*.json $P/d 2>&1 | head -30
