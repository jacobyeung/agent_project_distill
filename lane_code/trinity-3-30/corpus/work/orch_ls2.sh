cd /project/community/jjyeung/okh7 || exit 1
find . -mindepth 4 -maxdepth 4 \( -name "result.tar.gz" -o -name "*.tar.gz" \) -printf "%s %TY-%Tm-%Td %p\n" 2>/dev/null | grep -v -E "/(payload|bootstrap|kit|code|env)" | sort -k3 | awk '{s+=$1; printf "%.1fM %s %s\n",$1/1e6,$2,$3} END{printf "TOTAL %.2f GB %d\n", s/1e9, NR}'
echo ---dirs
ls -1
