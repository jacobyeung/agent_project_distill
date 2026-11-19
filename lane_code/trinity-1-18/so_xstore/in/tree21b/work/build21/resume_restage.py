from pathlib import Path
import sys, json
B=Path(__file__).resolve().parent
label=sys.argv[1]
for name in ('q','r1'):
    path=B/'kits'/name
    if path.exists():
        target=B/('retained_'+label+'_'+name)
        assert not target.exists(), target
        path.rename(target)
p=B/'KIT_Q_INITIAL.json'
if p.exists():p.rename(B/('retained_'+label+'_initial.json'))
(B/('RESTAGE_'+label+'.json')).write_text(json.dumps(dict(from_empty=True,GO=False,label=label)))
