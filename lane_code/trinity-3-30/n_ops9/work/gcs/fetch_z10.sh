W=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z10/out
sha256sum $W/kit_n/k/y.json $W/kit_n_go/k/y.json
grep -H ' k/y.json' $W/kit_n/SHA256SUMS.txt $W/kit_n_go/SHA256SUMS.txt
find $W -maxdepth 4 -name 'SESSION_NAMES*' -printf '%s %p\n' 2>/dev/null | head -5
for f in $(find $W -maxdepth 4 -name 'SESSION_NAMES.template.list' 2>/dev/null | head -1); do echo "@@T $f"; sha256sum $f; cat $f; echo "@@TEND"; done
echo "@@Y"; cat $W/kit_n/k/y.json; echo; echo "@@END"
