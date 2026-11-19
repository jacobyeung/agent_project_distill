S=/project/community/jjyeung/cp4tk_fr/k6tk
ls -la $S | cut -c1-120
zcat $S/MEMBERS.tsv.gz | wc -l
zcat $S/MEMBERS.tsv.gz | grep -m3 -E "5434c2265b166c943c3a67b94fcecce2ac913e7349f99409826c7cf959dc177f|7f8b99bfd9565ec8a1b8fad3450c21ee4f62be29c14b5118e55764b53bc739b0|f25faedce4622416aed654d13ed347ed2a3b1ea0928a5674a80169324c6888cc" | cut -c1-200
zcat $S/MAP.jsonl.gz | head -2 | cut -c1-400
head -c 600 $S/INDEX.json; echo; head -c 500 $S/RECEIPT.json; echo
ls $S/parts 2>/dev/null | head -5; ls $S/parts 2>/dev/null | wc -l
