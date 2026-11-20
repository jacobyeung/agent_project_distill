export TZ=UTC; X=/project/community/jjyeung/okh7/x_22c714e1; cd $X
grep -n "trap\|TERM\|cleanup" jd2.sh | cut -c1-220
python3 - <<'P'
import json
d=json.load(open('qd/k/j.json'))
print(type(d).__name__, list(d)[:10] if isinstance(d,dict) else '')
P
ls -ld /home/jjyeung/okit/i/eb3429c5/eb3429c5.tar /home/jjyeung/okit 2>&1 | head
sacct -j 173497,173496 -X -o JobID,Partition,State,Start,End,NodeList -n
