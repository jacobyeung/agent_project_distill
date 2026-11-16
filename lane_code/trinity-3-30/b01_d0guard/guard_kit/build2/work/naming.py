from pathlib import Path
from copy import deepcopy
import ast
import hashlib
import json
import sys
import tarfile
B=Path(__file__).resolve().parents[1];K=B/'out/guard_kit';W=B.parents[1]/'work'
sys.path.insert(0,str(K))
from guard_core import read,sha,write,digest
from names import BAD,neutral,rename,prove,scan_json
import packet
base=read(B/'out/inputs/BASELINE_CONFIG.json');mapping={}
def collect(value):
 if isinstance(value,str):
  if BAD.search(value):mapping[value]=neutral(value)
 elif isinstance(value,list):
  for v in value:collect(v)
 elif isinstance(value,dict):
  for k,v in value.items():collect(k);collect(v)
collect(base);projected=rename(base,mapping);prove(base,projected,mapping)
write(B/'out/NEUTRAL_CONFIG_PROJECTION.json',projected)
write(B/'out/TRINITY_NAME_MAP.json',mapping)
items=read(B/'out/inputs/items.json');keymap={k:neutral(k) for k in items['keys']}
write(B/'out/TRINITY_KEY_MAP.json',keymap)
write(B/'out/OPAQUE_ITEMS.json',rename(items,keymap))
meta=read(B/'out/candidate_m50/CLOSURE.json');files=packet.packed_files(meta)
raw_files=__import__('closure').members(W/'d0closure/closure_359fcc3c.tar')
if files!=raw_files:raise ValueError('Metadata names changed non-name bytes')
archive_hits=[]
with tarfile.open(meta['archive']['path']) as tar:
 for m in tar:
  if BAD.search(m.name):archive_hits.append(m.name)
occurrences=[]
for p in sorted(K.rglob('*')):
 if not p.is_file() or p.suffix not in ('.py','.json','.sh'):continue
 for number,line in enumerate(p.read_text().splitlines(),1):
  for match in BAD.finditer(line):
   occurrences.append(dict(file=str(p.relative_to(B)),line=number,column=match.start()+1,text=line[:900],
       classification='Code identifier/prose or runtime literal; preserved sealed source, not an exemption for operational names'))
with (B/'out/NAMING_OCCURRENCES.jsonl').open('w') as out:
 for v in occurrences:out.write(json.dumps(v,sort_keys=True)+'\n')
seal=read(W/'d0closure/x/k/7.json')
trainer=[name for name in seal['files'] if BAD.search(name)]
closure_hits=[]
for name,raw in files.items():
 if name.endswith('.json'):
  try:value=json.loads(raw)
  except ValueError:continue
  for h in scan_json(value):closure_hits.append(dict(file=name,**h))
write(B/'out/CLOSURE_NAMING_OCCURRENCES.json',closure_hits)
result=dict(status='PARTIAL_BLOCKED',outer_closure_member_hits=archive_hits,
    config_projection_roundtrip=True,projection_is_runtime_integrated=False,original_config_hits=scan_json(base),
    required_trainer_members_with_prohibited_names=trainer,trainer_tree_sha256=seal['tree_sha256'],
    code_occurrences_file='out/NAMING_OCCURRENCES.jsonl',closure_occurrences_file='out/CLOSURE_NAMING_OCCURRENCES.json',
    actual_runtime_item_keys_neutral=False,packet_top_level_hits=scan_json(read(B/'out/FAMILY.json')))
write(B/'out/NAMING.json',result)
write(B/'out/NAME_ROUNDTRIP.json',dict(status='PASS',scope='Outer candidate metadata member aliases and proposed config/item projections only',
    metadata_files=len(files),metadata_all_bytes_equal=True,metadata_archive_sha256=meta['archive']['sha256'],
    metadata_source_sha256=meta['source_sha256'],config_mapping_entries=len(mapping),item_mapping_entries=len(keymap),
    runtime_migration_complete=False))
print(json.dumps(dict(metadata_files=len(files),trainer_name_hits=len(trainer),config_hits=len(result['original_config_hits']),closure_hits=len(closure_hits))))
