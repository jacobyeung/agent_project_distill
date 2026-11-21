O=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z14/out; ls $O | head; F=$(ls $O/admit_test.py 2>/dev/null || ls $O/*.py | head -1); echo "file $F"; sha256sum $O/admit_test.sh $F | cut -c1-8,65-
grep -n "host_receipt_pin\|host_receipt_assertions\|def _host\|allowed offline\|ALLOWED\|--map\|offline" $F | head -30
n=$(grep -n "host_receipt_pin" $F | head -1 | cut -d: -f1); [ -n "$n" ] && sed -n "$((n-5)),$((n+45))p" $F
sed -n 1,40p $O/admit_test.sh
