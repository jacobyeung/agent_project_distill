"""Enumerate the successful proof and classify every requested text hit."""
from pathlib import Path
from collections import Counter
from unittest.mock import patch
import json
import os
import re
import sys

E = Path(__file__).resolve().parent
K = E.parent.parent
proof = json.loads((E/'proof_result.json').read_text())
root = Path(proof['job_root'])
work = root.parent
extracted = E/'extracted'
cfg = json.loads((root/'bootstrap/CONFIG.json').read_text())
prepared = json.loads((work/'prepared/CONFIG.json').read_text())
logical = prepared['spec']
orchard_root = '/tmp/'+root.name
records = [json.loads(line) for p in sorted((E/'records04').glob('*.jsonl'))
           for line in p.read_text().splitlines()]
paths = {'.': 'directory'}
for p in root.rglob('*'):
    paths[str(p.relative_to(root))] = 'symlink' if p.is_symlink() else 'directory' if p.is_dir() else 'file'
for r in records:
    p = Path(r.get('path','/'))
    if p.is_relative_to(root):
        paths.setdefault(str(p.relative_to(root)), 'transient write/create observed')
(E/'job_paths.tsv').write_text('kind\tpath_relative_to_job_root\n'+''.join(
    kind+'\t'+p+'\n' for p,kind in sorted(paths.items())))
argv = [r for r in records if 'argv' in r]
(E/'local_argv.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in argv))
projected = []
replacements = [
    (str(extracted/'launcher/test_runs'/prepared['token']/'pool'),prepared['pool']),
    (str(extracted),logical['package']),
    (cfg['spec']['run'],logical['run']),
    (cfg['spec']['package'],logical['package']),
    (str(work/'videos'),logical['inputs']['video_root']),
    (str(root/'m/ap'),'/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'),
    (str(root),orchard_root),
]
def project(arg):
    for before,after in replacements:
        arg = arg.replace(before,after)
    return arg

for r in argv:
    a = r['argv']
    if not isinstance(a,list):
        raise ValueError('Unexpected shell argv')
    projected.append(dict(kind='projected_'+r['kind'],function=r.get('function'),
        argv=[project(s) for s in a],note='Derived from observed local call; not executed on Orchard.'))

sys.path.insert(0,str(extracted/'launcher'))
import orchard_job as J
import orchard_launcher as L
import orchard_stage as S
# Namespace construction is read-only; use production media pins, not fixture pins.
with patch.object(J,'physical',return_value=extracted):
    ns = J.namespace(root,prepared)
chain_command = ns+[logical['interpreters']['vllm'],'-s','-B',str(root/'bootstrap/trace_runtime.py'),
    '--script',str(Path(logical['package'])/'reader/chain.py'),'--root',str(root),
    '--config',str(root/'bootstrap/CONFIG.json')]
projected.append(dict(kind='assembled_namespace',argv=[s.replace(str(root),orchard_root) for s in chain_command],
    note='Unmodified namespace builder with prepared config and production media manifest; no process launched.'))
projected.append(dict(kind='assembled_sbatch',argv=L.submit_argv(None,prepared['token'],proof=True),
    note='Unmodified submission argv builder; not submitted.'))
transport=json.loads((extracted/'launcher/TRANSPORT.json').read_text())
for part in transport['parts']:
    projected.append(dict(kind='production_export_fetch',argv=['gcloud','storage','cat',
        'gs://cmu-gpucloud-jjyeung/'+part['name']+'#'+str(part['generation'])],
        note='Pinned transport replaces the observed local fixture stream; not fetched.'))
(E/'orchard_argv.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in projected))

base_names=json.loads((E/'baseline/build/BASE_FILES.json').read_text())
base_root=Path(json.loads((K.parent/'kit/proof/PASS3_LOCAL_RELEASE/RESULT.json').read_text())['job_root'])
def canonical(p):
    return re.sub(r'^sj/a[a-f0-9]+/', 'sj/TOKEN/',p)
base_paths={canonical(str(p.relative_to(base_root))) for p in base_root.rglob('*')}
terms=['split','revsi','vsi','vsibench','distill','qgen','scannet','arkit','qwen','legs1','rv_merge','official','bench']
def classify(value,source,term):
    if source == 'local_argv' and term not in project(value).lower():
        return 'NEW LOCAL ONLY','local audit/extraction prefix; not an Orchard path'
    if canonical(value) in base_paths:
        return 'PRE-EXISTING','same relative path in reviewed VSI local proof'
    for name in base_names:
        if value.endswith('/'+name) or value == name or value.endswith('/'+Path(name).name):
            return 'PRE-EXISTING','kit file name shared with reviewed VSI kit: '+name
    if '/orch_cd/legs1_reads' in value or '/orch_cd/rv_merge_fix' in value:
        return 'PRE-EXISTING','unchanged alias paths in chain.py and proof/phase_b.py; not launcher-only'
    if str(K) in value or str(extracted) in value:
        return 'NEW LOCAL ONLY','local audit/extraction prefix; not an Orchard path'
    if 'fixture' in value:
        return 'LOCAL FIXTURE','substituted local transport/model fixture'
    return 'NEW OR UNCLASSIFIED','requires review; no pre-existing provenance asserted'
rows=[]
for path in sorted(paths):
    for term in terms:
        if term in path.lower():
            status,reason=classify(path,'job_root',term)
            rows.append(('job_root',path,term,status,reason))
for label,commands in [('local_argv',argv),('orchard_argv',projected)]:
    for i,r in enumerate(commands):
        for j,s in enumerate(r['argv']):
            for term in terms:
                if term in s.lower():
                    status,reason=classify(s,label,term)
                    rows.append((f'{label}[{i}].argv[{j}]',s,term,status,reason))
(E/'path_hits.tsv').write_text('source\tstring\tterm\tstatus\treason\n'+''.join('\t'.join(r)+'\n' for r in rows))
counts={term:dict(Counter(r[3] for r in rows if r[2]==term)) for term in terms}
summary=dict(job_root=str(root),paths=len(paths),local_commands=len(argv),
    orchard_commands=len(projected),hits=len(rows),terms=counts,
    new_or_unclassified=[r for r in rows if r[3]=='NEW OR UNCLASSIFIED'])
(E/'inventory_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
