"""Exercise the config patch against local copies of the live round-5 state."""
import hashlib,json,os,subprocess
from pathlib import Path
H=Path(__file__).resolve().parents[1];OUT=H/'evidence/fix6_patch';OUT.mkdir()
old=H/'evidence/fix6_before/payload';manifest=json.loads((H/'evidence/fix6_patch_manifest.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results={}
def fixture(name):
 top=OUT/name;top.mkdir(mode=0o700);b=top/'i_1be16f28';b.mkdir(mode=0o700)
 for p in old.iterdir():
  if p.name in manifest:(b/p.name).write_bytes(p.read_bytes())
  else:os.link(p,b/p.name)
 for n in ('review.json','staging.json'):
  v=json.loads((b/n).read_text());v.update(verdict='PASS',status='PASS',reviewer='fixture-only',missing=[]);(b/n).write_text(json.dumps(v))
 for n in ('p','e','q'):
  (b/n).mkdir();(b/n/'marker').write_text('old derived fixture')
 for n in ('p.json','e.json','c.json','archive.json','gate.json','ready.json','result.json','compare.json','anon.json','go.json'):(b/n).write_text('{"fixture":"old"}')
 kh=top/'x_4b3114cf';kh.mkdir();(kh/'ANON_OK.json').write_text('old certificate');(kh/'sess.json').write_text('unused fixture sessions')
 (b/'a.json').write_text('routing fixture');(b/'t').mkdir();(b/'t/marker').write_text('unchanged trainer extraction')
 p=top/'patch.sh';p.write_text((H/'build/c_patch.sh').read_text().replace('/project/community/jjyeung/okh7/i_1be16f28',str(b)))
 return top,b,p

def snapshot(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def run(name,top,b,p,good):
 before=snapshot(top);r=subprocess.run(['/bin/bash',str(p)],capture_output=True,text=True)
 (OUT/(name+'.log')).write_text(r.stdout+r.stderr)
 assert (r.returncode==0)==good,(name,r.stderr)
 if not good:assert snapshot(top)==before
 results[name]='PASS'

top,b,p=fixture('good');before=snapshot(top);run('live_patch',top,b,p,True)
for n in manifest:
 assert sha(b/n)==sha(H/'payload'/n)
 assert sha(b/'v_6'/n)==before['i_1be16f28/'+n]
assert snapshot(top/'x_4b3114cf')=={'ANON_OK.json':before['x_4b3114cf/ANON_OK.json'],'sess.json':before['x_4b3114cf/sess.json']}
assert sha(b/'a.json')==before['i_1be16f28/a.json'] and sha(b/'t/marker')==before['i_1be16f28/t/marker']
assert not (b/'p').exists() and (b/'v_6/p/marker').exists()
assert not (b/'go.json').exists() and (b/'v_6/go.json').exists()
run('repeat',top,b,p,False)
for label,n in [('bad_deriver','d.py'),('bad_sums','sums.txt')]:
 top,b,p=fixture(label);(b/n).write_text('altered');run(label,top,b,p,False)
top,b,p=fixture('foreign_review');(b/'review.json').write_text('{"config_sha256":"wrong"}');run('foreign_review',top,b,p,False)
top,b,p=fixture('new_kit_exists');(top/'x_3fdda0fb').mkdir();run('new_kit_exists',top,b,p,False)
top,b,p=fixture('embedded_corrupt');s=p.read_text();pos=s.index("'data': '")+len("'data': '");p.write_text(s[:pos]+('A' if s[pos]!='A' else 'B')+s[pos+1:]);run('embedded_corrupt',top,b,p,False)
(OUT/'results.json').write_text(json.dumps(dict(status='PASS',cases=results,old_kit_untouched=True,runtime_evidence_retained=True,trainer_archive_reused=True),indent=2)+'\n')
print(json.dumps(results))
