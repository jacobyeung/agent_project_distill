F=/project/community/jjyeung/cp4tk_fr/k6tk
ls $F | head -20
ls $F/parts | head -5; ls $F/parts | wc -l
for f in INDEX.json RECEIPT.json; do echo "== $f"; head -c 600 $F/$f 2>/dev/null; echo; done
