from pathlib import Path
import datetime,sys
B=Path(__file__).resolve().parent
p=B/'STATUS.md'
with p.open('a') as f:f.write('\n'+datetime.datetime.now(datetime.timezone.utc).isoformat()+' '+ ' '.join(sys.argv[1:])+'\n')
