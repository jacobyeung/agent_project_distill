import ast,hashlib,json,pathlib,re,shlex,tarfile,tokenize
B=pathlib.Path(__file__).resolve().parents[1];A=B.parents[1];O=B/'out';K=O/'guard_kit'
import sys
sys.path.insert(0,str(K));from guard_core import read,sha,write,digest
from names import rename,prove,scan_json,BAD
base=read(O/'BASELINE_CONFIG.json');fam=read(O/'BASELINE_FAMILY.json')
# A flattened baseline ledger retains every original scalar, including administrative pins.
flat={}
def leaves(v,path):
 if isinstance(v,dict):
  for k,x in v.items():leaves(x,path+'/'+k)
 elif isinstance(v,list):
  for i,x in enumerate(v):leaves(x,path+'/'+str(i))
 else:flat[path]=v
leaves(base,'CONFIG');leaves(fam,'FAMILY');write(O/'BASELINE_PIN_VALUES.json',flat)
# Operational source paths can be copied byte-for-byte under neutral names.
renames={};copies=[]
for key,value in flat.items():
 if isinstance(value,str) and value.startswith('/project/community/jjyeung/') and BAD.search(value):
  new='/project/community/jjyeung/okh7/8c9d2e74/'+hashlib.sha256(value.encode()).hexdigest()[:16]
  renames[value]=new
  parent='/'.join(key.split('/')[:-1]);pin=flat.get(parent+'/sha256')
  if not any(x['old']==value for x in copies):copies.append(dict(old=value,new=new,sha256=pin))
normalized=rename(base,renames);prove(base,normalized,renames)
write(O/'OPERATIONAL_NAME_MAP.json',renames);write(O/'NEUTRAL_CONFIG_PROPOSAL.json',normalized)
write(O/'NAME_ROUNDTRIP.json',dict(pass_operational_renaming=True,all_other_json_scalars_equal=True,source=str(O/'BASELINE_CONFIG.json'),proposal=str(O/'NEUTRAL_CONFIG_PROPOSAL.json'),remaining=scan_json(normalized)))
# Exact kernel and copied source evidence.
source=A/'work/c8r_code'; records=[]
for p in sorted(source.rglob('*')):
 if p.is_file():
  q=K/p.relative_to(source);records.append(dict(path=str(p.relative_to(source)),original=sha(p),current=sha(q),equal=p.read_bytes()==q.read_bytes()))
write(O/'SOURCE_IDENTITY.json',dict(sealed_tar=sha(B/'in_c8r_kit/code_c8r.tar'),files=records,all_equal=all(x['equal'] for x in records)))
# List every textual occurrence in shipped code, with file and line.
hits=[]
for p in sorted(K.rglob('*')):
 if not p.is_file() or p.suffix not in ('.py','.json','.sh'):continue
 for i,line in enumerate(p.read_text().splitlines(),1):
  for match in BAD.finditer(line):
   hits.append(dict(file=str(p.relative_to(K)),line=i,column=match.start()+1,word=match.group(),text=line[:700],reason='Inherited sealed source or reviewed stager; identifiers/prose may be permitted, literal job-visible paths and scope names remain unresolved.'))
with (O/'NAMING_OCCURRENCES.jsonl').open('w') as f:
 for row in hits:f.write(json.dumps(row,sort_keys=True)+'\n')
write(O/'NAMING_SCAN.json',dict(status='BLOCKED',code_occurrences=len(hits),config_occurrences=len(scan_json(normalized)),archive_member_hits=[str(p.relative_to(K)) for p in K.rglob('*') if BAD.search(str(p.relative_to(K)))],inventory='out/NAMING_OCCURRENCES.jsonl',job_visible_metadata='out/NAME_ROUNDTRIP.json'))
lines=['# Naming','', 'Release is blocked. Operational source-path renaming is reversible and preserves all other JSON scalars (`NAME_ROUNDTRIP.json`). It does not complete job-visible metadata renaming.', '', 'Every textual occurrence in the code tree is listed with file, line, column and context in `NAMING_OCCURRENCES.jsonl`. CONFIG occurrences are listed in `NAME_ROUNDTRIP.json`; counts and archive-member results are in `NAMING_SCAN.json`.', '', 'The original kernels contain capture-scope names. Prepared metadata and request item keys also carry names that are authenticated by nested digests. Replacing those strings changes the request/preparation identities. The current worker retains original keys to preserve C8r admission. `TRINITY_KEY_MAP.json` and `inputs/opaque_reference.json` provide the proposed opaque mapping; they are not a completed runtime migration.', '', 'Code identifiers and explanatory prose are not operational names. Literal path, item-key and capture-scope occurrences need a complete migration or an explicit ruling before this family can launch. No such ruling is assumed.', '', 'Orchard operator copies (identical bytes; never executed here):','```sh','mkdir -p /project/community/jjyeung/okh7/8c9d2e74']
for row in copies:
 lines+=['cp -- '+shlex.quote(row['old'])+' '+shlex.quote(row['new']),'sha256sum -- '+shlex.quote(row['old'])+' '+shlex.quote(row['new'])]
 if row['sha256']:lines+=['# Required SHA256: '+row['sha256']]
lines+=['```',''];(O/'NAMING.md').write_text('\n'.join(lines))
# Measure timings without printing large decode traces.
ret=A/'work/ret544';r=read(ret/'native/R1.json');s=read(ret/'metadata/STAGING.json');j=read(ret/'metadata/ORCHARD_NATIVE.json');admit=read(ret/'native/paired/IN_JOB_ADMISSION.json')
phase={k:v['seconds'] for k,v in s.items() if isinstance(v,dict) and 'seconds' in v}
ns=sum(x['seconds'] for x in r['arms']['unflagged']);ss=sum(x['seconds'] for x in r['arms']['scripted']);sel=read(O/'inputs/items.json');by={x['key']:x for x in r['arms']['unflagged']}
proof=sum(by[k]['seconds'] for k in sel['proof_keys']);geom=admit['geometry_seconds'];gpu=j['gpu_phase_seconds'];staging=sum(phase.values());load=max(0,gpu-ns-geom)
# Conservatively prepare the full geometry cohort for both exports.
need=staging+phase['export']+phase['export_headers']+2*geom+ns+proof+2*load
margin=max(3600,need*.35);limit=5*3600
sizing=dict(sources=dict(staging=str(ret/'metadata/STAGING.json'),job=str(ret/'metadata/ORCHARD_NATIVE.json'),items=str(ret/'native/R1.json'),admission=str(ret/'native/paired/IN_JOB_ADMISSION.json')),phase_seconds=phase,native_item_seconds=ns,scripted_record_seconds=ss,geometry_seconds=geom,residual_load_parity_seconds=load,proof_item_seconds=proof,need_seconds=need,margin_seconds=margin,requested_seconds=limit,request_covers_estimate=limit>=need+margin,assumptions=['candidate native decode duration equals accepted checkpoint; no measured guarantee','both exports prepare the complete capture cohort','canary rows are reused; no additional full-arm duplicates','second export transfer duration estimated from reference transport','full runtime/base/exports are not present locally'])
write(O/'SIZING.json',sizing)
# All unchanged semantic backend inputs are separately pinned.
ind={k:v for k,v in fam['worker_contract'].items() if k not in ('config','data_receipt')}
ind['assets']={k:v for k,v in fam['assets'].items() if k not in ('small_objects','worker_entrypoint')}
write(O/'INDEPENDENT_CONTRACT.json',ind)
print(json.dumps(dict(naming_hits=len(hits),native_seconds=ns,scripted_seconds=ss,need=need,margin=margin,limit=limit),indent=2))
