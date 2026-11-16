set +e
C=/project/community/jjyeung
ls -la $C/cp4tk_eval $C/cp4tk_eval/official | head -60
wc -l $C/cp4tk_eval/official/meta_5130.jsonl; sha256sum $C/cp4tk_eval/official/meta_5130.jsonl; head -c 1200 $C/cp4tk_eval/official/meta_5130.jsonl; echo
python3 -c "
import json,collections
c=collections.Counter(); v=set()
for l in open('$C/cp4tk_eval/official/meta_5130.jsonl'):
    r=json.loads(l); c[r.get('question_type')]+=1; v.add((r.get('dataset'),r.get('scene_name')))
print(dict(c)); print(len(v))
"
timeout 60 find $C/cp4tk_eval -maxdepth 3 \( -iname '*score*' -o -iname '*summary*' -o -iname '*result*' \) -printf '%s %TY-%Tm-%TdT%TH:%TM %p\n' 2>/dev/null | head -30
