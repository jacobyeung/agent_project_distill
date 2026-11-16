from pathlib import Path
import ast,hashlib,json,subprocess,tarfile
L=Path(__file__).resolve().parents[1];O=L/'out';W=L/'work';B=W/'base/work/base/tree_b01ce449'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
manifest=json.loads((O/'PATCH_MANIFEST_R6.json').read_text())
inventory={p.relative_to(B).as_posix():sha(p) for p in B.rglob('*') if p.is_file()}
seal=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert seal==manifest['base_seal'],seal
proof=json.loads((O/'APPLY_PROOF_R6.json').read_text());checks=[]
for name,tree in [('base',W/'trees/r6_applied'),('tree_r1',W/'trees/r6_snapshot')]:
 for rel,item in manifest['files'].items():
  expected=item.get('accepted_integration_bases',[item])[0]['patched_sha256'] if name=='tree_r1' else item['patched_sha256']
  assert sha(tree/rel)==expected,(name,rel)
  assert sha(W/'src_r6'/rel)==item['patched_sha256'],rel
 if name=='base':
  for rel,digest in inventory.items():
   if rel not in manifest['files']:assert sha(tree/rel)==digest,rel
 else:
  with tarfile.open(W/'tree_r1/tree_r1_build1_fab2eea8.tar') as archive:
   for member in archive:
    if not member.isfile():continue
    rel=Path(*Path(member.name).parts[1:]).as_posix()
    if rel not in manifest['files']:assert sha(tree/rel)==hashlib.sha256(archive.extractfile(member).read()).hexdigest(),rel
 checks.append(dict(tree=str(tree),patched_hashes_match=True,untouched_files_equal=True))
for name,digest in manifest['patch_sha256'].items():assert sha(O/name)==digest,name
for record in proof.values():
 transaction=Path(record['apply']['stdout'].split('retained original: ')[1].strip()).parent
 for p in transaction.glob('*.diff.log'):
  text=p.read_text();assert not any(x in text.lower() for x in ('offset','fuzz','reject','failed')),text
source=ast.parse((W/'src_r6/student_pilot/geometry_profiles.py').read_text())
reference=ast.parse((W/'ref/gravity_guard_a62e3975_recovered.py').read_text())
def guard(t):return [ast.dump(n) for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='validate_up_convention' or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='UP_PLANE_MIN' for x in n.targets)]
assert guard(source)==guard(reference)
result=dict(base_seal=seal,base_source=str(B),guard_ast_equal=True,guard_reference=str(W/'ref/gravity_guard_a62e3975_recovered.py'),
 patched_trees=checks,ordered_zero_fuzz_offset=True,source_sha256={p.relative_to(W/'src_r6').as_posix():sha(p) for p in (W/'src_r6').rglob('*.py')})
with (O/'PACKET_INTEGRITY_R6.json').open('x') as f:json.dump(result,f,indent=2)
coverage=json.loads((W/'coverage_detail_r6.json').read_text());assert not coverage['uncovered']
with (O/'COVERAGE_DETAIL_R6.json').open('x') as f:json.dump(coverage,f,indent=2)
lines=[f'Every executable line added by the source/test interdiff ran in the applied-tree suites or named coverage probes. Source: [coverage detail]({O}/COVERAGE_DETAIL_R6.json).',
'| Source line | Disposition | Test |','|---|---|---|']
for r in coverage['records']:
 lines.append(f"| [{Path(r['source']).name}:{r['line']}]({r['source']}:{r['line']}) | {'Executed' if r['executed'] else r['reason']} | {'; '.join(r['tests'][:2])} |")
with (O/'CHANGED_LINE_COVERAGE_R6.md').open('x') as f:f.write(lines[0]+'\n\n'+'\n'.join(lines[1:])+'\n')
print('Packet hashes, unchanged files, guard AST, and changed-line coverage verified.')
