O=/project/community/jjyeung/okh7
cd $O
for d in 7c9f2d84 7c9f2d84_bundle 7c9f2d84_in x_07ca49df; do echo "== $d"; ls -la $d | head -25; done
echo "== depth-3 receipt.json under 7c9f2d84* and x_07ca49df (bounded)"
timeout 60 find 7c9f2d84 7c9f2d84_bundle 7c9f2d84_in x_07ca49df -maxdepth 5 \( -name 'receipt.json' -o -name 'rows.sqlite' -o -name '*.tar' \) -size -200M -printf '%s %p\n' 2>/dev/null | head -60
