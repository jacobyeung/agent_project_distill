export TZ=UTC
K=/project/community/jjyeung/okh7/x_69d2930d
ls -la --time-style=+%m-%dT%H:%M $K/runs/673bc60f | awk '{print $5,$6,$7}'
ls -la --time-style=+%m-%dT%H:%M $K/runs/673bc60f/m100 $K/runs/673bc60f/m200 | awk '{print $5,$6,$7}'
ls -la --time-style=+%m-%dT%H:%M /project/community/jjyeung/okh7/r/673bc60f | awk '{print $5,$6,$7}'
grep -E "slot|persist|checkpoint" $K/o/171377.steps | tail -8 | cut -c1-200
python3 -c "
import json;a=json.load(open('$K/runs/673bc60f/m200/artifact.json'));print(sorted(a.keys()));print({k:(v if not isinstance(v,(dict,list)) else type(v).__name__) for k,v in a.items()})" 2>&1 | cut -c1-900
ls -la --time-style=+%H:%M /project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs | awk '{print $5,$6,$7}'
