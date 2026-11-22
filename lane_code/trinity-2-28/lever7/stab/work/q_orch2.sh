P=/project/community/jjyeung
echo "== r2/sj"; ls -la $P/okh7/e6fc152498/r2/sj/ 2>&1 | head -30
echo "== r2"; ls $P/okh7/e6fc152498/r2/ 2>&1 | head -30
for d in $P/okh7/e6fc152498/r2/sj/h10sub*; do [ -d "$d" ] && echo "-- $d" && ls -la "$d" | head -8 && [ -f "$d/items.jsonl" ] && sha256sum "$d/items.jsonl" && wc -l < "$d/items.jsonl"; done
echo "== gcs"; (command -v gsutil >/dev/null && timeout 60 gsutil ls gs://cmu-gpucloud-jjyeung/q8/ae71c903/ 2>&1 | grep -E 'b01ec87a6f29b' ; timeout 60 gsutil ls -l gs://cmu-gpucloud-jjyeung/q8/ae71c903/b01ec87a6f29b00029a87/ 2>&1 | head) || echo no-gsutil
