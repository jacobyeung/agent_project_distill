export TZ=UTC; scontrol show job 170674 | grep -o -E "(MinMemory|mem|TRES|NumCPUs)[^ ]*" | head
python3 - <<'P'
import json
p='/tmp/a170674b01ec87a6f29b/sj/b01ec87a6f29b/r/metadata/journals/3/0/environment.json'
try:
  e=json.load(open(p)); print(e['binding']['ids'][:5], len(e['binding']['ids']))
except Exception as x: print('noread', x)
P
