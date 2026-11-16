O=/project/community/jjyeung/okh7; B=$O/i_1be16f28
grep -v ': OK$' $O/t_c94bbc4e.log | tail -n 10 | cut -c1-300
cat $B/staging.json; echo; cat $B/archive.json; echo; python3 -c "import json;d=json.load(open('$B/c.json'));print({k:(v if not isinstance(v,(list,dict)) else len(v)) for k,v in d.items()})"
