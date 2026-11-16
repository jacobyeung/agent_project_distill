from pathlib import Path
import difflib,dis,json,types
L=Path(__file__).resolve().parents[1];out=L/'out';base=L/'work/base/work/base/tree_b01ce449';tree=L/'work/trees/tree_r1_rehearsal'
groups=json.loads((L/'work/patch_groups.json').read_text());trace={}
for tag in ('B2_INTEGRATION','B2_FINAL','B2_FIXTURE_FINAL','B2_COVERAGE_EXTRA','B2_TREE_RUNNABLE'):
    p=out/f'{tag}_trace.json'
    if not p.exists():continue
    for rel,lines in json.loads(p.read_text()).items():
        for n,tests in lines.items():trace.setdefault(rel,{}).setdefault(n,set()).update(tag+':'+t for t in tests)
def executable(code):
    lines={n for _,n in dis.findlinestarts(code) if n>0}
    for c in code.co_consts:
        if isinstance(c,types.CodeType):lines.update(executable(c))
    return lines
report={}
for group,files in groups.items():
    rows=[]
    for rel in files:
        a=(base/rel).read_text().splitlines() if (base/rel).exists() else []
        source=(L/'work/src'/rel).read_text();b=source.splitlines();actual=(tree/rel).read_text().splitlines()
        mapping={}
        for op,i,j,k,n in difflib.SequenceMatcher(None,b,actual,autojunk=False).get_opcodes():
            if op=='equal':mapping.update({z+1:k+z-i+1 for z in range(i,j)})
        changed=set()
        for op,i,j,k,n in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
            if op in ('insert','replace'):changed.update(range(k+1,n+1))
        for line in sorted(changed & executable(compile(source,rel,'exec'))):
            integrated=mapping[line];tests=sorted(trace.get(rel,{}).get(str(integrated),set()))
            rows.append(dict(file=rel,line=line,integration_line=integrated,source=b[line-1].strip(),tests=tests))
    report[group]=dict(total=len(rows),executed=sum(bool(r['tests']) for r in rows),lines=rows)
report['geometry_on_tree_r1']=dict(report['geometry'],note='Identical contract statements; routing statement locations use integration_line. Rebase only shifts hunks around the preserved next-leg event-row branch.')
(out/'COVERAGE_DETAIL_B2.json').write_text(json.dumps(report,indent=2)+'\n')
text=['# Changed executable-line coverage','',f'Source: `{out}/COVERAGE_DETAIL_B2.json`. Every listed test was run on `{tree}`. The trace harness records Python line events; it does not imply branch coverage.','', '| Patch | Executed | Changed executable lines |','|---|---:|---:|']
for group,v in report.items():text.append(f"| {group} | {v['executed']} | {v['total']} |")
text+=['','## Statement evidence','','| Patch | File:source line → integration line | Executing test |','|---|---|---|']
for group,v in report.items():
    for r in v['lines']:
        tests='; '.join(r['tests'][:2]) or 'NOT EXECUTED — requires resolution before integration'
        text.append(f"| {group} | `{r['file']}:{r['line']} → {r['integration_line']}` | {tests} |")
(out/'CHANGED_LINE_COVERAGE_B2.md').write_text('\n'.join(text)+'\n')
for group,v in report.items():
    print(group,v['executed'],v['total'])
    for r in v['lines']:
        if not r['tests']:print(r['file'],r['line'],r['source'])
