"""Run review algorithms with only local paths/layout adapted."""
from pathlib import Path
import sys,json,io,contextlib,collections
W=Path.cwd();O=W/'out';P=O/'src'
sys.path.insert(0,str(P/'orchard_h10/vendor'));import chain_save
# The supplied reproducer hard-codes its obsolete layout. Retain it unchanged;
# adapt its fixture paths to the new returned metadata layout and all six types.
s=(W/'in/refute_members.py').read_text()
s=s.replace("'/scratch/jjyeung/orch_n30/review_rr1b1p/new/orchard_h10/vendor'",repr(str(P/'orchard_h10/vendor')))
s=s.replace("'/scratch/jjyeung/orch_n30/review_rr1b1p/t/r_'",repr(str(W/'work/tmp/r_')))
s=s.replace('((0,3),(1,3),(0,0),(0,4))','((0,3),(0,0),(0,1),(0,2),(0,4),(1,3))')
s=s.replace("f'{i}/metadata/", "f'metadata/reads/{i}/metadata/")
s=s.replace("f'{i}/{t}/metadata/journals/{t}/0/", "f'metadata/reads/{i}/metadata/journals/{t}/0/")
s=s.replace("f'{i}/{t}/", "f'metadata/reads/{i}/metadata/journals/{t}/0/")
(W/'work/refute_members.py').write_text(s)
ns={};exec(compile(s,str(W/'work/refute_members.py'),'exec'),ns)
assert len([n for n in ns['m'] if n.endswith('items.jsonl')])==6
# Run the reviewer's exact scanner code with old/new resolved to payload roots.
s=(W/'in/eat.py').read_text();s=s.replace("f'{side}/{x}'", "str(roots[side]/x)").replace('root=side','root=roots[side]')
(W/'work/reviewer_eat.py').write_text(s)
proof={}
for label,old in [('bf94',W.parent/'b1p/out/baseline'),('a943',W.parent/'b1f/out/src'),('e47',W.parent/'b1p/out/src')]:
 buf=io.StringIO();ns={'roots':{'old':old,'new':P}}
 with contextlib.redirect_stdout(buf):exec(compile(s,'reviewer_eat.py','exec'),ns)
 print(label,buf.getvalue());proof[label]=dict(stdout=buf.getvalue(),added=list((ns['res']['new']-ns['res']['old']).elements()),removed=list((ns['res']['old']-ns['res']['new']).elements()))
assert not proof['a943']['added']
(O/'REVIEWER_EAT.json').write_text(json.dumps(proof,indent=2)+'\n')
