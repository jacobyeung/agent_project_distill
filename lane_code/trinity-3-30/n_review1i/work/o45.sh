X=/project/community/jjyeung/okh7/x_22c714e1; TZ=UTC date +%TZ
python3 -c "
import json;v=json.load(open('$X/o/174113/q0.json'))
print('steps',v.get('steps')); print('forward',json.dumps(v.get('forward'))[:600]); print('refusal',v.get('refusal'))
" < /dev/null
tail -c 2500 $X/o/174113/q.steps < /dev/null
grep -n -i "traceback\|cuda\|error" $X/o/174113/q.log < /dev/null | tail -20 | cut -c1-300
ls $X/o/174113_live < /dev/null; tail -c 1500 $X/o/174113_live/t_q.log < /dev/null 2>/dev/null | cut -c1-300
