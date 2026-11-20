cd /project/community/jjyeung/okh7/x_22c714e1/o/JOB || exit 1
date -u +%TZ; ls -la . live 2>/dev/null | head -40
for f in routing_selection.json receipt.json materialization.json db_bytes.json dbb.log; do [ -f $f ] && { echo "@@@ $f $(stat -c %s $f) $(sha256sum < $f | cut -c1-64)"; base64 -w0 $f; echo; }; done
