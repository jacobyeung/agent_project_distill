cd /project/community/jjyeung || exit 1
ls -la cp4tk_fr/k6tk | head -20
head -c 1500 cp4tk_fr/k6tk/RECEIPT.json; echo; head -c 800 cp4tk_fr/k6tk/INDEX.json; echo
zcat cp4tk_fr/k6tk/MEMBERS.tsv.gz | head -3; zcat cp4tk_fr/k6tk/MAP.jsonl.gz | head -2 | cut -c1-400
ls -la okh7/x_ee227714/k | grep -i "frame\|\.tar\|k.json" | head
ls -la distill/okit/in/cr | grep -v "\.ok$" | awk '{print $5, $9}' | sort -k2 | awk '{s+=$1; print} END {print "TOTAL", s}' | tail -45
