P=/project/community/jjyeung/okh7
cd $P || exit 1
ls | wc -l
ls -d *_fetched 2>/dev/null | head -50
echo ---
find . -maxdepth 3 -name "result.tar.gz" -printf "%s %TY-%Tm-%Td %p\n" 2>/dev/null | sort -k3 | awk '{s+=$1; printf "%.1fM %s %s\n",$1/1e6,$2,$3} END{printf "TOTAL %.2f GB %d\n", s/1e9, NR}'
