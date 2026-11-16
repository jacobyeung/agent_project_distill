"""Publish validated row-family evidence and its source-bound summary."""
from pathlib import Path
from collections import Counter
import json
L=Path(__file__).resolve().parents[2]; W=Path(__file__).resolve().parent; O=L/'out'
data=json.loads((W/'comparison.json').read_text())
validation=json.loads((W/'validation.json').read_text())
integrity=json.loads((W/'integrity.json').read_text())
reference=json.loads((O/'ROW_FAMILY_PARITY_R3.json').read_text())
assert validation['all_evidence_checks_pass'] and integrity['all_hashes_match'] and integrity['under_limit']
assert not data['defects']
data['status']='PASS'
data['validation']=validation;data['integrity']=integrity
data['inventory']=json.loads((W/'inventory.json').read_text())
data['summary']['semantic_program_families']=len(next(c['detail'] for c in validation['checks'] if c['name']=='native_semantic_family_enumeration'))
data['summary']['source_path']=str(O/'ROW_FAMILY_PARITY_R5.json')
data['candidate_binding_source']=str(W/'candidate_bindings.json')
data['unrenderable_with_supplied_inputs']=reference['unrenderable_with_supplied_inputs']
for item in data['unrenderable_with_supplied_inputs']:
    if 'evidence' in item:item['evidence']=str(W/'base.json')
data['scope_notes']=[
 'Every family rendered by the sealed base renders in both epochs. Complete returned rows are compared without field filtering.',
 'All ON rows are audited with their declared synthetic GT candidate binding. Unbound verdicts remain in each sample.',
 'Structured point-program events use the same formatter in the generator and auditor. Native POOL membership gates still reject infrastructure-only v1 point programs.',
 'The sensor session retains the fused provider. Predicted-mode and MDG provider selection follows the explicit runtime contract.',
 'The camera pool exclusion authority and full surface-converter source package are absent. Native camera leaves and surface/extent sessions are covered; full pool/converter execution is not claimed.',
 'CPU fixtures prove renderer and audit contracts; they do not measure model answer quality.'
]
old={r['family']:r for r in reference['families']}
for r in data['families']:
    r['production_source_paths']=old[r['family']]['production_source_paths']
    r['patched_production_source_paths']=[p.replace('r6_r3','r4_proof/base') for p in old[r['family']]['patched_production_source_paths']]
    r['on_contract_changes']=dict(Counter(d['contract_change'] for s in r['samples'] for d in s['differences']))
data['writing_note']='No project-history statements are retained; base/OFF/ON identify controlled test arms.'
J=O/'ROW_FAMILY_PARITY_R5.json';J.write_text(json.dumps(data,indent=2)+'\n')
s=data['summary']; source=f'[JSON evidence]({J})'
lines=[f'All base-renderable families pass OFF byte parity. Every ON difference is mapped, and every ON row passes its contract audit. Source: {source}.',
 f'The fixtures cover {s["semantic_program_families"]} semantic families across {s["families"]} renderer/family groups. Base, OFF and ON each render {s["rendered_rows"]["base"]} rows; ON admits {s["on_audits"]["admitted"]}. Source: {source}.',
 'Each table value comes from the linked family artifacts. The JSON retains every delta, byte hash, refusal, audit verdict and candidate binding.',
 '| Family | Base / OFF / ON | OFF parity | ON admitted | Mapped changes | Sources |',
 '|---|---:|---|---:|---|---|']
for r in data['families']:
    n=r['rows_per_arm'];paths=r['source_paths'][:3]
    lines.append(f'| {r["family"]} | {n["base"]} / {n["off"]} / {n["on"]} | {"PASS" if n["base"] else "matching refusal"} | {r["audit_counts"].get("admitted",0)} | {", ".join(r["on_contract_changes"]) or "unchanged"} | '+ ' '.join(f'[artifact]({p})' for p in paths)+' |')
lines += ['',*data['scope_notes'],f'Storage and file hashes: [integrity]({W}/integrity.json).']
(O/'ROW_FAMILY_PARITY_R5.md').write_text('\n\n'.join(lines[:3])+'\n\n'+'\n'.join(lines[3:])+'\n')
