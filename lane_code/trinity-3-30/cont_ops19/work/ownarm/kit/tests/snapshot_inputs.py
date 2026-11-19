"""Materialize local test inputs from the snapshot; never claim an Orchard run.

A4 is accepted only if reconstruction reproduces its reviewed archive hash.
The A templates reproduce b200 with the kit's embedded dry checks added.
The strict scorer fixture combines pinned reference rows with synthetic metadata.
Usage: python snapshot_inputs.py FRESH_WORK_DIR
"""
import json,re,sys
from pathlib import Path

KIT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(KIT))
import build_ownread as B
import ownread

def main(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=False)
 base=KIT.parent/'out/pkg/b200';d=B.unpack((base/'1.tgz').read_bytes())
 p=B.unpack(d['0.tgz']);bundle=B.bundle_of(d['BATCH.sh'])
 # Reverse the supplied unified diff in memory, checking every context line.
 lines=d['a/6.py'].decode().splitlines(True);out=[];pos=0
 patch=(KIT/'OPERATOR_DIFF_VS_A4.patch').read_text().splitlines(True);i=2
 while i<len(patch):
  m=re.match(r'@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@',patch[i]);assert m,patch[i]
  start=int(m[1])-1;out.extend(lines[pos:start]);pos=start;i+=1
  while i<len(patch) and not patch[i].startswith('@@'):
   line=patch[i];i+=1
   if line[0] in ' +':assert lines[pos]==line[1:];pos+=1
   if line[0] in ' -':out.append(line[1:])
 out.extend(lines[pos:]);operator=''.join(out).encode()
 assert B.sha(operator)==B.A4_OPERATOR_SHA256
 refs,rows=ownread.references()
 token='d60a20ec01296' # A4 token recorded in the supplied OWNREAD_REPORT.md.
 new,_,_,_,raw=B.seal(d,p,bundle,token,operator)
 expected=json.loads((base/'BUILD.json').read_text())['diff_vs_a4']
 assert B.sha(raw)==B.A4_DELIVERY_SHA256,{'token':token,'mismatches':{n:B.sha(v) for n,v in new.items() if B.sha(v)!=expected[n]['a4_sha256']}}
 a4=root/'A4';B.put(a4/'1.tgz',raw);B.put(a4/'tower_sequence.py',operator)
 for n in ('fetch_return.py','unpack_return.py'):B.put(a4/n,(base/n).read_bytes())
 a=root/'A';a.mkdir()
 old_token=(base/'TOKEN').read_text().strip()
 for script in sorted(base.glob('o_*.sh')):
  text=script.read_text().replace(old_token,'d72cdcff1e22a')
  if script.name=='o_place.sh':text=text.replace(B.sha((base/'1.tgz').read_bytes()),'ca977dd2bc6feb1c14c7c03023eefe7b5e2b67b1cabe838d34effbafd003c765')
  if script.name.startswith('o_pullfill'):
   text=text.replace('E=$A/a/e\n','B=/project/community/jjyeung/okh7/a15_cot_apb9188e9225a85\nE=$A/a/e\n')
   text=text.replace('test -f "$A/0.tgz"\n','test -f "$A/0.tgz"\ntest -f "$B/0.tgz"\n')
  (a/script.name).write_text(text)
 B.put(a/'READ_PLAN.json',(base/'READ_PLAN.json').read_bytes())
 derived=B.scripts(a,old_token,B.sha((base/'1.tgz').read_bytes()),json.loads(p['9.json'])['export_binding'],None)
 assert all(text==(B.add_dry_checks((base/n).read_text()) if n.startswith('o_pullfill')
                   else (base/n).read_text()) for n,text in derived.items())
 # Test data, not a measured or authenticated return.
 ret=root/'proof/ret_strict';plan=json.loads((base/'READ_PLAN.json').read_text())
 binding=plan['export_binding'];pin=dict(binding,preparation={k:{'sha256':v} for k,v in binding['preparation_sha256'].items()})
 inputs={'archives':[{'sha256':binding['archive_sha256']}]}
 identity=dict(plan=plan['plan_sha256'],operator_sha256=B.sha(d['a/6.py']),reads=plan['read_settings'],cards=1,inputs=B.canonical(inputs))
 for name,value in [('IDENTITY',identity),('EXPORT_PIN',pin),('INPUTS',inputs)]:B.put(ret/('metadata/'+name+'.json'),B.jbytes(value))
 manifest=json.loads(p['items/devs1_routed.json']);order=json.loads(p['9.json'])['order']
 for t in range(3):
  ids=[item['id'] for item in manifest['items'] if item['question_type']==order[t]]
  envbinding=dict(refs['tower200']['binding'],arms=['tower','own'],modes=[{'name':'none'}],fixture=False,
                  count=manifest['count'],shard='0/1',ids=ids)
  env={'binding':envbinding,'settings':refs['tower200']['settings']}
  journal=ret/'metadata/reads/0/metadata/journals'/str(t)/'0'
  B.put(journal/'environment.json',B.jbytes(env))
  B.put(journal/'items.jsonl',(''.join(json.dumps(rows[name][k])+'\n' for name in ('tower200','own544') for k in ids)).encode())
 print(json.dumps({'a4_sha256':B.sha(raw),'script_roundtrip':True,'synthetic_scorer_fixture':str(ret),'root':str(root)}))

if __name__=='__main__':main(sys.argv[1])
