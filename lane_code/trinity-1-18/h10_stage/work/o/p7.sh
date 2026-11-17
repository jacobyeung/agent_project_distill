P=/project/community/jjyeung/okh7
cat $P/i_1be16f28/e.json; echo; ls -laR $P/i_1be16f28/e | head -30
python3 -c "
import json;d=json.load(open('$P/i_bb09a77d/E00_MEMBERS.json'));print(json.dumps(d)[:2500])"
cat $P/i_1be16f28/archive.json; echo
