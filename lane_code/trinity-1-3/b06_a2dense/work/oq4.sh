C=/project/community/jjyeung/cp4tk_fr
for d in media plan stage_in bin gcs logs; do echo "== $d"; ls -la $C/$d | head -15; echo "n=$(ls -f $C/$d | wc -l)"; done
ls -la $C/k6tk | head; ls $C/k6tk/parts | head; ls -f $C/k6tk/parts | wc -l
head -c 800 $C/k6tk/INDEX.json; echo; head -c 800 $C/k6tk/RECEIPT.json; echo; head -c 600 $C/k6tk/VALIDATION.json; echo
zcat $C/k6tk/MEMBERS.tsv.gz | head -3; zcat $C/k6tk/MEMBERS.tsv.gz | wc -l
