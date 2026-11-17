"""Compare only the seven changed closure members with the retained D0 archive."""
import ast,difflib,json,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'tools'))
import selection_check as sc
old=sc.load(H/'payload/d_f232d4160d75b582.json')['implementation'];new=sc.load(H/'evidence/fix7_selection/implementation.json')
changed={n for n in old.keys()|new.keys() if old.get(n)!=new.get(n)}
assert len(changed)==7
records={}
with tarfile.open(H/'evidence/derivation/d0/k/t_b01ce449beffe35b.tar') as tf:
 for n in sorted(changed):
  current=(H/'build/tree'/n).read_text();previous=tf.extractfile(n).read().decode() if n in old else ''
  if previous:assert __import__('hashlib').sha256(previous.encode()).hexdigest()==old[n]
  def definitions(text):
   return {node.name:(ast.dump(node,include_attributes=False),node.lineno) for node in ast.parse(text).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
  a,b=definitions(previous),definitions(current)
  records[n]=dict(recorded=old.get(n),actual=new.get(n),changed_definitions={k:b.get(k,(None,None))[1] for k in a.keys()|b.keys() if a.get(k,(None,))[0]!=b.get(k,(None,))[0]})
  if previous:
   (H/'evidence/fix7_selection'/(Path(n).stem+'.diff')).write_text(''.join(difflib.unified_diff(previous.splitlines(True),current.splitlines(True),n,n)))
# Verify the directly executed selector/filter/validator modules, not just the entrypoint.
 names=['student_pilot/s1_pool.py','student_pilot/ground_rows.py','student_pilot/row_removals.py','student_pilot/s1_exclusions.py','student_pilot/s1_scene_census.py','student_pilot/p3_provenance.py']
 for n in names:assert old[n]==new[n]
 # The two changed routing helpers are never called by prepare or its row validators.
 assert set(records['student_pilot/carrier_c1_routing.py']['changed_definitions'])=={'finish','encode_own'}
(H/'evidence/fix7_selection/changes.json').write_text(json.dumps(dict(changed=records,unchanged_selector_modules=names),indent=2)+'\n')
print(json.dumps({n:list(v['changed_definitions']) for n,v in records.items()},indent=2))
