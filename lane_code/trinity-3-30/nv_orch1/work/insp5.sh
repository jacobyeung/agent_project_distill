cd /project/community/jjyeung/b9ef552934627
python3 -c "
import json; d=json.load(open('a/1.json')); print(json.dumps(d, indent=0)[:6000])"
