O=/project/community/jjyeung/okh7
cd $O
n=0
for t in $(timeout 60 find . -maxdepth 3 -name '*.tar' -size -400M 2>/dev/null); do n=$((n+1)); timeout 30 tar tf $t 2>/dev/null | grep -E 'r16|vxm_m4|5e1d07a4|7c9f2d84' | sed "s#^#$t: #" | head -5; done
echo "tars scanned $n"
