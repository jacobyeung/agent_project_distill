P=/project/community/jjyeung/okh7
cat $P/a15_cot_apda6f7936c1779/a/export.json; echo; cat $P/a15_cot_apda6f7936c1779/a/e/5; echo; head -c 1500 $P/a15_cot_apda6f7936c1779/a/e/7; echo
python3 -c "import json;d=json.load(open('$P/a15_cot_apda6f7936c1779/a/1.json'));print(list(d.keys()) if isinstance(d,dict) else type(d))"
grep -o '"[a-z_]*export[a-z_]*"[^,]*' $P/a15_cot_apda6f7936c1779/a/1.json | head; grep -o '5083243c[0-9a-f]*' $P/a15_cot_apda6f7936c1779/a/*.json | sort -u | head
ls $P/b7e31d84a90c62f5/170235/; ls $P/b7e31d84a90c62f5/170235/* | head
