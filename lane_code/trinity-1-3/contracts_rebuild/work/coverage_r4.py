from pathlib import Path
import difflib,dis,json,types
L=Path(__file__).resolve().parents[1];O=L/'out';S=L/'work/src_r4';B=L/'work/base/work/base/tree_b01ce449'
groups=json.loads((L/'work/patch_groups_r4.json').read_text());trace={}
for tag in ('B7_FINAL_R4','B7_SNAPSHOT_R4','B7_EDGES_R4','B7_SNAPSHOT_EDGES_R4'):
    path=L/f'work/{tag}_trace.json'
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
(O/'COVERAGE_DETAIL_R4.json').write_text(json.dumps(report,indent=2)+'\n')
text=['# Changed executable-line coverage','',f'Source: [COVERAGE_DETAIL_R4.json]({O}/COVERAGE_DETAIL_R4.json). Tracing records executed source lines on the applied tree. Execution is not an assertion-coverage claim. Mutation tests independently check the reviewed failure modes; see [MUTATION_R4.json]({O}/MUTATION_R4.json).','',
      '| Patch | Executed | Changed executable lines |','|---|---:|---:|']
for group,v in report.items():text.append(f"| {group} | {v['executed']} | {v['total']} |")
text+=['','| Patch | Source | Tests |','|---|---|---|']
for group,v in report.items():
    for r in v['lines']:
        tests='; '.join(r['tests'][:2]) or 'Not executed in this CPU suite.'
        text.append(f"| {group} | [{r['file']}:{r['line']}]({S/r['file']}:{r['line']}) | {tests} |")
text+=['',f'The integration snapshot preserves its event-row and preparation branches. Its hashes and ordered application checks are in [APPLY_PROOF_R4.json]({O}/APPLY_PROOF_R4.json); its suite outcome is in [FINAL_TEST_RESULTS_R4.json]({O}/FINAL_TEST_RESULTS_R4.json).']
(O/'CHANGED_LINE_COVERAGE_R4.md').write_text('\n'.join(text)+'\n')
for group,v in report.items():
    print(group,v['executed'],v['total'])
    for r in v['lines']:
        if not r['tests']:print(r['file'],r['line'],r['source'])
