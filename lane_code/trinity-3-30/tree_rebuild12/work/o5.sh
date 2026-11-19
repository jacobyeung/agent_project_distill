P=/project/community/jjyeung; cd $P/okh7; ls; cat h_6ed2c7aa/m400/DONE.json 2>&1 | head -c 600; echo
timeout 120 find $P/okh7 -maxdepth 4 -name '*m400.tar.part*' 2>/dev/null | head; timeout 60 find $P/okh7 -maxdepth 4 -name 'tokenizer_config.json' 2>/dev/null | head -5
which gsutil gcloud 2>&1 | head -2; ls $P/okh7/x_22c714e1/q/k/; python3 -c "
import json;d=json.load(open('$P/okh7/x_22c714e1/q/k/p.json'));print(list(d.keys()));print(d.get('p_root'),d.get('milestone'),d.get('namespace'))" 2>&1 | head -c 1500
