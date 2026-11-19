J=/project/community/jjyeung/okh7
S=$J/h_6ed2c7aa/m400/s.tar
echo "== b83 tree"; tar xOf $S files/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/k/t_b83a8a35d420815b.tar | tar tf - | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -rn | head -30
echo "== b01 tree"; tar tf $J/x_07ca49df/k/t_b01ce449beffe35b.tar 2>/dev/null | awk -F/ '{print $1"/"$2}' | sort | uniq -c | sort -rn | head -30
ls -la $J/x_07ca49df/k | grep t_
python3 -c "
import json;s=json.load(open('$J/x_ee227714/k/7.json'));print(s.get('schema'),s.get('commit'),len(s.get('files',{})));print(sorted(set(k.split('/')[0] for k in s.get('files',{}))))
print([k for k in s if k!='files'])"
