K=/project/community/jjyeung/okh7
TZ=UTC squeue -u $USER -o '%i %j %P %T %M %l %R' 2>&1 | head
for p in a15_cot_apd7a6db629db02 a15_cot_apdacd91c2f5c4b a15_cot_apdc863c3e6b41d a15_cot_apdd982cd5c4b25; do echo "== $p"; ls -la $K/$p/a/f 2>&1 | head -8; cat $K/$p/a/8.txt 2>/dev/null; done
ls $K/813f42db/c21h544r | head -30
df -BG $K | tail -1
