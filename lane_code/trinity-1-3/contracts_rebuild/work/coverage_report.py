from pathlib import Path
import difflib
import dis
import json
import types
import sys
L=Path(__file__).resolve().parents[1]
base=L/'work/base/work/base/tree_b01ce449'
src=L/'work/src'
trace=json.loads((L/f'out/{sys.argv[1]}_trace.json').read_text())
groups=json.loads((L/'work/patch_groups.json').read_text())
def executable(code):
    lines={n for _,n in dis.findlinestarts(code) if n>0}
    for c in code.co_consts:
        if isinstance(c,types.CodeType):lines.update(executable(c))
    return lines
report={}
for group,files in groups.items():
    rows=[]
    for rel in files:
        old=(base/rel).read_text().splitlines() if (base/rel).exists() else []
        text=(src/rel).read_text();new=text.splitlines()
        changed=set()
        for op,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
            if op in ('insert','replace'):changed.update(range(c+1,d+1))
        lines=changed & executable(compile(text,rel,'exec'))
        for line in sorted(lines):
            tests=trace.get(rel,{}).get(str(line),[])
            rows.append(dict(file=rel,line=line,source=new[line-1].strip(),tests=tests))
    report[group]=dict(total=len(rows),executed=sum(bool(r['tests']) for r in rows),lines=rows)
(L/'out/COVERAGE_DETAIL.json').write_text(json.dumps(report,indent=2))
for group,v in report.items():
    print(group,v['executed'],v['total'])
    for r in v['lines']:
        if not r['tests']:print(r['file'],r['line'],r['source'])
