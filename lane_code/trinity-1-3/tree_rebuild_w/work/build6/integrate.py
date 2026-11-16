"""Authenticate packet, stage unchanged patches, and port each hunk explicitly."""
import ast, difflib, hashlib, json, re, subprocess
from pathlib import Path
L=Path(__file__).resolve().parents[2]
B=L/'work/build6'; P=L/'work/contracts_r6'; T=L/'work/tree_r1'; S=B/'integrate'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
manifest=json.loads((P/'PATCH_MANIFEST_R6.json').read_text())
write(B/'STATUS.md','# Build 6 status\n\nIntegrating authenticated packet hunks; no suites have run yet.\n')
write(B/'DECISIONS.md','# Build 6 decisions\n\nUse the original packet base for three-way integration. Preserve the existing level_basis function byte for byte. Keep simulated GT recovery admission with contracts OFF; require the packet training audit with contracts ON. These defaults preserve earlier behavior while adding the accepted contract.\n')
for name,digest in manifest['patch_sha256'].items(): assert sha(P/name)==digest,name
rows=[]; chunks={}
for group in ('geometry','candidates','box'):
    name=f'PATCH_{group}_r6.diff'
    for chunk in re.split(r'(?=^--- a/)',(P/name).read_text(),flags=re.M):
        if not chunk.strip():continue
        rel=chunk.splitlines()[0][6:];chunks[rel]=chunk
for rel,e in manifest['files'].items():
    before=sha(T/rel); base=L/'work/base/tree_b01ce449'/rel
    assert sha(base)==e['base_sha256'],rel
    for folder,source in [('base',base),('patched',base),('current',T/rel),('result',T/rel)]:
        if source.exists():write(S/folder/rel,source.read_text())
    route='exact' if before==e['base_sha256'] else 'merged'
    rows.append(dict(file=rel,before=before,route=route,manifest_patched=e['patched_sha256'],hunks=[]))
for group in ('geometry','candidates','box'):
    name=f'PATCH_{group}_r6.diff'
    result=subprocess.run(['patch','--batch','--forward','-p1','-F0','--no-backup-if-mismatch','-d',str(S/'patched'),'-i',str(P/name)],capture_output=True,text=True)
    write(S/(name+'.log'),result.stdout+result.stderr)
    assert result.returncode==0,result.stdout
    assert not re.search('fuzz|offset|FAILED',result.stdout),result.stdout
for row in rows:
    rel=row['file']; patched=(S/'patched'/rel).read_text();assert sha(S/'patched'/rel)==row['manifest_patched']
    current=(T/rel).read_text() if (T/rel).exists() else ''
    result=current
    for index,hunk in enumerate(re.split(r'(?=^@@ )',chunks[rel],flags=re.M)[1:],1):
        lines=hunk.splitlines(keepends=True);old=''.join(s[1:] for s in lines[1:] if s.startswith((' ','-')))
        new=''.join(s[1:] for s in lines[1:] if s.startswith((' ','+')))
        record=dict(hunk=index,header=lines[0].strip(),disposition='applied verbatim')
        if row['route']=='exact':pass
        elif result.count(old)==1:result=result.replace(old,new,1)
        elif rel=='student_pilot/ground_rows.py' and index==1:
            # The packet replaces the membership guard. Earlier builds also admit
            # audited simulated GT misses; that legacy path must remain OFF.
            start=result.index('    simulated = ');end=result.index('    validate_evidence(record)',start)
            prior=result[start:end]
            simulated=prior[:prior.index('    if (record.get')]
            adapted=simulated+new[new.index('    from trace_format.contracts'):new.index('    validate_evidence(record)')]
            adapted=adapted.replace('(record.get("not_seen") and not recovery)', '(record.get("not_seen") and not recovery and not (not new_contracts() and simulated))')
            result=result[:start]+adapted+result[end:]
            record.update(disposition='adapted',reason='Retain build 1–5 simulated GT recovery admission OFF; run the packet audit for every ON recovery.',adaptation=''.join(difflib.unified_diff(new.splitlines(True), (new[:new.index('    from trace_format.contracts')]+adapted+'    validate_evidence(record)\n    target, spans, _ = render_ground(row["events"], row["answer"])\n').splitlines(True),fromfile='packet hunk',tofile='integrated hunk')))
        else:
            record['disposition']='conflicting';row['hunks'].append(record)
            write(B/'INTEGRATION.json',json.dumps(rows,indent=2));raise SystemExit('Conflicting hunk: '+rel+' '+str(index))
        row['hunks'].append(record)
    if row['route']=='exact':result=patched
    ast.parse(result);write(S/'result'/rel,result)
    row['after']=sha(S/'result'/rel)
    if row['route']=='exact':assert row['after']==row['manifest_patched']
old=ast.parse((T/'student_pilot/carrier_c1_routing.py').read_text());new=ast.parse((S/'result/student_pilot/carrier_c1_routing.py').read_text())
assert ast.dump(next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='level_basis'))==ast.dump(next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='level_basis'))
protection=json.loads((L/'work/build5/proofs/artifact_locations/PROTECTION.json').read_text())
protected={p['path'] for p in protection['paths']}
for row in rows:
    rel=row['file'];assert 'work/tree_r1/'+rel not in protected
    assert sha(T/rel)==row['before'];write(T/rel,(S/'result'/rel).read_text())
write(B/'INTEGRATION.json',json.dumps(rows,indent=2)+'\n')
report=['# Contract integration\n','Source: `work/build6/INTEGRATION.json`. Packet files and their hashes remain unchanged. The staged base accepts each original patch with zero fuzz and zero offset.\n']
for row in rows:
    report += [f"## {row['file']}\n",f"Route: {row['route']}. Before: `{row['before']}`. After: `{row['after']}`. Manifest: `{row['manifest_patched']}`.\n",'| Hunk | Disposition | Reason |\n|---|---|---|']
    report += [f"| {h['header']} | {h['disposition']} | {h.get('reason','Unchanged packet text.')} |" for h in row['hunks']]
    report += ['\n```diff\n'+h['adaptation']+'```\n' for h in row['hunks'] if 'adaptation' in h]
write(L/'out/CONTRACTS_INTEGRATION.md','\n'.join(report)+'\n')
write(B/'STATUS.md','# Build 6 status\n\nContract integration installed. Per-file hashes and every hunk disposition: `work/build6/INTEGRATION.json`. Packet and tree suites remain pending.\n')
print(json.dumps(dict(files=len(rows),exact=sum(r['route']=='exact' for r in rows),merged=[r['file'] for r in rows if r['route']=='merged'])))
