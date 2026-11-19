from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];source=W/'code/assemble_final.py';scope={'__file__':str(source)}
exec(compile(source.read_text().split('reports={',1)[0],str(source),'exec'),scope)
inputs={str(source):hashlib.sha256(source.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};results={}
for a,b in [('BASE','NEW'),('LIVE_BASE','LIVE')]:
 pa=W/'out'/('FOCUSED_'+a+'.json');pb=W/'out'/('FOCUSED_'+b+'.json')
 for p in (pa,pb):inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 r=scope['compare'](json.loads(pa.read_text()),json.loads(pb.read_text()));results[a+'_'+b]=r
 print(a,b,r['status'],r['new_failure_signatures'])
(W/'out/FOCUSED_COMPARISON.json').write_text(json.dumps(dict(input_sha256=inputs,comparisons=results,command='python code/compare_focused.py'),indent=2)+'\n')
