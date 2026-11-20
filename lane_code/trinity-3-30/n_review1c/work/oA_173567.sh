cd /project/community/jjyeung/okh7/x_22c714e1/o/173567 || exit 1
date -u +%TZ; ls -la . live 2>/dev/null | head -40
for f in routing_selection.json receipt.json materialization.json db_bytes.json dbb.log; do [ -f $f ] && { echo "@@@ $f $(stat -c %s $f) $(sha256sum < $f | cut -c1-64)"; base64 -w0 $f; echo; }; done
echo "@@@ steps"; tail -15 q.steps 2>/dev/null; ls -la live | head; for f in q1.json r1.json; do [ -f $f ] && cat $f; echo; done
tail -5 /project/community/jjyeung/okh7/x_22c714e1/j/a15_cot_ap24d9b8e2_173567.log 2>/dev/null
