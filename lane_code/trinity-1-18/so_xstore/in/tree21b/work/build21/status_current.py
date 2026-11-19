from pathlib import Path
import datetime,json,sys
B=Path(__file__).resolve().parent
def get(p):return json.loads(p.read_text()) if p.exists() else {}
state=get(B/'ITEMS.json')
if len(sys.argv)>2:state[sys.argv[1]]=dict(status=' '.join(sys.argv[2:]),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(B/'ITEMS.json').write_text(json.dumps(state,indent=2)+'\n')
lines=['Build 21 status','',*['Item '+str(i)+': '+state.get(str(i),{}).get('status','Pending')+' (source: work/build21/ITEMS.json).' for i in range(1,6)]]
if (B/'DELIVERY.json').exists():lines+=['','Delivery: work/build21/DELIVERY.json. Report: out/BUILD21_REPORT.md.']
(B/'STATUS.md').write_text('\n\n'.join(lines)+'\n')
