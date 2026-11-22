W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; cd $W/work || exit 1
for j in d173864/173864 d173881/173881 d173817/173817; do echo "$j $(sha256sum $j/routing_selection.json $j/receipt.json $j/materialization.json 2>&1 | cut -c1-8 | tr '\n' ' ') $(grep -o '5e35c3ce' $j/db_bytes.json 2>/dev/null | head -1)"; done
grep -h -o 'c_8ae781f4x[^ ]*' $W/../tree_rebuild22/work/*.sh 2>/dev/null | sort -u | head
