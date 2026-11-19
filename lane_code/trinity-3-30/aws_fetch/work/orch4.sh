O=/project/community/jjyeung/okh7
cd $O
echo "B64R"; base64 -w0 7c9f2d84/receipt.json; echo
timeout 90 find . -maxdepth 4 \( -iname '*r16*' -o -iname '*vxm*' -o -name 'h' \) -printf '%y %s %p\n' 2>/dev/null | head -40
echo "== receipts small, sha"
timeout 120 find . -maxdepth 4 -name 'receipt.json' -size -200k -print0 2>/dev/null | xargs -0 -r sha256sum 2>/dev/null | grep -E '^(9a7f3310|524b14f9)' | head
timeout 120 find . -maxdepth 4 -name 'receipt.json' -size -200k 2>/dev/null | wc -l
