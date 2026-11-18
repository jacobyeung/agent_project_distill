cat /home/jjyeung/okit/j/07ca49df.sh
KH=$(grep -oE '^KH=[^ ]+' /home/jjyeung/okit/j/07ca49df.sh | head -1 | cut -d= -f2 | tr -d '"')
echo "KH=$KH"; ls -la "$KH" 2>&1 | head; du -sh "$KH/k" "$KH/b" 2>&1 | head
ls -la "$KH/k/np226_5204b3a0.tar" "$KH/k/t_e6456bcecb8d4a8f4f68158eb68275f8befff128.tar" 2>&1; cat "$KH/ANON_OK.json" 2>&1 | head -c 600
