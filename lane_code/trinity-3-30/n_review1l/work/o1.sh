export TZ=UTC; date -u +%TZ
X=/project/community/jjyeung/okh7/x_22c714e1
for j in 173881 173912 173964 173966; do [ -d $X/o/$j ] && { echo "== $j"; ls $X/o/$j | head -40 | tr '\n' ' '; echo; sha256sum $X/o/$j/routing_selection.json $X/o/$j/receipt.json 2>/dev/null | cut -c1-16,65-; }; done
sha256sum $X/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73 | cut -c1-16
head -c 1500 $X/u/a49f117f60add326e1ef3e8eb2b92a73ec299425e8efb477fa9e84d462789e73; echo
