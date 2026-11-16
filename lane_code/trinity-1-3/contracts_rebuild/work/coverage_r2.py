from pathlib import Path
import difflib,dis,json,types
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r2';B=L/'work/base/work/base/tree_b01ce449'
groups=json.loads((L/'work/patch_groups_r2.json').read_text());trace={}
for tag in ('R2_FINAL_APPLIED','R2_EXTRA'):
    path=O/f'{tag}_trace.json'
    if not path.exists():continue
    assert path.stat().st_size<20_000_000
    for rel,lines in json.loads(path.read_text()).items():
        for n,tests in lines.items():trace.setdefault(rel,{}).setdefault(n,set()).update(tag+': '+t for t in tests)
def executable(code):
    lines={n for _,n in dis.findlinestarts(code) if n>0}
    for c in code.co_consts:
        if isinstance(c,types.CodeType):lines.update(executable(c))
    return lines
report={}
for group,files in groups.items():
    rows=[]
    for rel in files:
        a=(B/rel).read_text().splitlines() if (B/rel).exists() else []
        source=(S/rel).read_text();b=source.splitlines();changed=set()
        for op,i,j,k,n in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
            if op in ('insert','replace'):changed.update(range(k+1,n+1))
        for line in sorted(changed & executable(compile(source,rel,'exec'))):
            tests=sorted(trace.get(rel,{}).get(str(line),set()))
            rows.append(dict(file=rel,line=line,source=b[line-1].strip(),tests=tests))
    report[group]=dict(total=len(rows),executed=sum(bool(r['tests']) for r in rows),lines=rows)
(O/'COVERAGE_DETAIL_R2.json').write_text(json.dumps(report,indent=2)+'\n')
text=['# Changed executable-line coverage','',f'Source: `{O}/COVERAGE_DETAIL_R2.json`. Python line events were collected on the applied tree. Counts refer to executed lines, not branch coverage.','', '| Patch | Executed | Changed executable lines |','|---|---:|---:|']
for group,v in report.items():text.append(f"| {group} | {v['executed']} | {v['total']} |")
text+=['','| Patch | File:line | Test or integration reachability |','|---|---|---|']
for group,v in report.items():
    for r in v['lines']:
        tests='; '.join(r['tests'][:2]) or 'NOT EXECUTED: requires resolution before completion'
        text.append(f"| {group} | `{r['file']}:{r['line']}` | {tests} |")
text+=['','The integration variant preserves the snapshot’s event-row branch and has the same contract statements. Hash and zero-fuzz application evidence is in `APPLY_PROOF_R2.json`. Its added contract lines map to the geometry rows above; routing lines after the snapshot insertion shift by the preserved branch length.']
(O/'CHANGED_LINE_COVERAGE_R2.md').write_text('\n'.join(text)+'\n')
for group,v in report.items():
    print(group,v['executed'],v['total'])
    for r in v['lines']:
        if not r['tests']:print(r['file'],r['line'],r['source'])
