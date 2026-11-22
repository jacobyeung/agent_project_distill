export TZ=UTC; date -u +%TZ
X=/project/community/jjyeung/okh7/x_22c714e1; O=$X/o/174415
ls -la $O | head -40
for f in routing_selection.json receipt.json db_bytes.json materialization.json; do [ -f $O/$f ] && { sha256sum $O/$f; wc -c < $O/$f; }; done
B=$X/n/u/ca0616dbc67cf9a257774b43a9d5b134957b3f3ce0451e6bf5378f3d7d0c1984; sha256sum $B; wc -c < $B
ls -la $X/n/u | grep -E "c672ad47|da19bb3a|a49f117f|53faadaa" 
for f in routing_selection.json receipt.json db_bytes.json; do echo "BEGIN_$f"; [ -f $O/$f ] && [ $(wc -c < $O/$f) -lt 3000000 ] && gzip -9c $O/$f | base64 -w0; echo; echo "END_$f"; done
echo "BEGIN_base"; [ $(wc -c < $B) -lt 3000000 ] && gzip -9c $B | base64 -w0; echo; echo END_base
