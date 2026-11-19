cd /project/community/jjyeung/okh7 || exit 1
for d in a15_cot_ap* r j n2r x27ret 813f42db; do find $d -maxdepth 3 \( -name "*.tgz" -o -name "*.tar.gz" -o -name "EXIT.json" -o -name "RETURN_RECEIPT.json" \) -printf "%s %TY-%Tm-%TdT%TH:%TM %p\n" 2>/dev/null; done | sort -k3 | awk '{printf "%.1fM %s %s\n",$1/1e6,$2,$3}'
