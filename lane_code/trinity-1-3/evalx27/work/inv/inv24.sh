set +e
C=/project/community/jjyeung/cp4tk_eval/eval/cells
for c in f17ref_vsi f17tk_vsi; do echo "==== $c"; cat $C/$c/cell_label.json; echo; ls -la $C/$c/score $C/$c/run; python3 -c "
import json;d=json.load(open('$C/$c/score/scores.json'));print(json.dumps(d,indent=1)[:2500])"; done
