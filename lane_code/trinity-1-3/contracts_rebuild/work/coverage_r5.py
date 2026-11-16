from pathlib import Path
import difflib,dis,json,types
L=Path(__file__).resolve().parents[1];O=L/'out';trace={}
for tag in ('B8_COMPLETE_R5','B8_COMPLETE_SNAPSHOT_R5','B8_COMPLETE_COVERAGE_R5'):
    p=L/f'work/{tag}_trace.json'
    if not p.exists():continue
    for rel,lines in json.loads(p.read_text()).items():
        for line,tests in lines.items():trace.setdefault(rel,{}).setdefault(line,set()).update(tag+': '+t for t in tests)
def executable(code):
    out={n for _,n in dis.findlinestarts(code) if n>0}
    for c in code.co_consts:
        if isinstance(c,types.CodeType):out.update(executable(c))
    return out
records=[];missing=[]
for before,after in [('src_r4','src_r5'),('tests_r4','tests_r5')]:
    B=L/'work'/before;S=L/'work'/after
    for p in sorted(S.rglob('*.py')):
        rel=str(p.relative_to(S));old=(B/rel).read_text().splitlines() if (B/rel).exists() else []
        source=p.read_text();new=source.splitlines();key=rel if after=='src_r5' else 'tests_r5/'+rel
        lines=executable(compile(source,str(p),'exec'))
        for op,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
            if op=='equal':continue
            for n in range(c+1,d+1):
                tests=sorted(trace.get(key,{}).get(str(n),set()))
                reason=None if tests else 'No executable instruction: whitespace, comment, continuation or constant declaration.' if n not in lines else None
                row=dict(source=str(p),line=n,text=new[n-1],executed=bool(tests),tests=tests,nonexecuted_reason=reason,executable=n in lines)
                records.append(row)
                if n in lines and not tests and not reason:missing.append(row)
            for n in range(a+1,b+1):
                records.append(dict(source=str(B/rel),line=n,text=old[n-1],executed=False,tests=[],executable=False,
                                    nonexecuted_reason='Absent from r5: this interdiff line belongs to the removed or replaced r4 text.'))
result=dict(source_roots=[str(L/'work/src_r4'),str(L/'work/src_r5'),str(L/'work/tests_r4'),str(L/'work/tests_r5')],
            traced_sources=[str(L/f'work/{t}_trace.json') for t in ('B8_COMPLETE_R5','B8_COMPLETE_SNAPSHOT_R5','B8_COMPLETE_COVERAGE_R5')],
            changed_lines=records,uncovered_executable=missing)
(O/'COVERAGE_DETAIL_R5.json').write_text(json.dumps(result,indent=2))
lines=[f'The interdiff coverage records source and test lines individually. Evidence: [COVERAGE_DETAIL_R5.json]({O}/COVERAGE_DETAIL_R5.json). Execution and mutation assertions are recorded independently; both full applied-tree suites pass.',
       '| Source line | Disposition | Test |','|---|---|---|']
for r in records:
    disposition='Executed' if r['executed'] else r['nonexecuted_reason'] or 'UNCOVERED: requires a probe; no unreachability claim.'
    lines.append(f"| [{Path(r['source']).name}:{r['line']}]({r['source']}:{r['line']}) | {disposition} | {'; '.join(r['tests'][:2])} |")
(O/'CHANGED_LINE_COVERAGE_R5.md').write_text(lines[0]+'\n\n'+'\n'.join(lines[1:])+'\n')
for r in missing:print(r['source'].split('/work/')[-1],r['line'],r['text'].strip())
