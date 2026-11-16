"""Adapt the C8r executable-line census; never infer coverage from test success."""
import ast
from collections import Counter,defaultdict
import difflib
from pathlib import Path
import sys
B=Path(__file__).resolve().parents[1];R=B.parents[1]
sys.path.append(str(B/'code'))
from adapter import *
import coverage
from coverage.parser import PythonParser


def compact(lines):
    values=sorted(lines);result=[]
    if not values:return ''
    start=last=values[0]
    for n in values[1:]:
        if n==last+1:last=n;continue
        result.append(str(start) if start==last else f'{start}-{last}');start=last=n
    result.append(str(start) if start==last else f'{start}-{last}')
    return ','.join(result)


def labels(path):
    tree=ast.parse(path.read_text());labels={}
    for node in ast.walk(tree):
        if isinstance(node,ast.ClassDef) and node.name=='NativeBoundary':
            for n in range(node.lineno,node.end_lineno+1):labels[n]=('GPU decode','real restoration, prefill, generation and parity')
        if isinstance(node,ast.FunctionDef):
            if path.name=='proof.py' and node.name=='run':
                for n in range(node.lineno,node.end_lineno+1):labels[n]=('GPU decode','historical greedy repeats require a card')
            if path.name=='venue.py' and node.name=='packet':
                for n in range(node.lineno,node.end_lineno+1):labels[n]=('Orchard-only staging','remote packet construction')
            if path.name in ('perception.py','read_runtime.py') and node.name in ('generate','load_model'):
                for n in range(node.lineno,node.end_lineno+1):labels[n]=('GPU decode','checkpoint restoration or sampled GPU logits')
            if path.name=='geometry.py' and node.name=='prepare':
                for n in range(node.lineno,node.end_lineno+1):labels[n]=('GPU decode','inherited card preparation path')
        if isinstance(node,ast.If) and any(isinstance(x,ast.Raise) for x in node.body):
            for child in node.body:
                for n in range(child.lineno,child.end_lineno+1):labels[n]=('error branch with condition',ast.unparse(node.test))
    if path.name=='orchard.py' or 'orchard_native' in path.parts or path.name.startswith('orchard_'):
        parser=PythonParser(filename=str(path));parser.parse_source()
        for n in parser.statements:labels.setdefault(n,('Orchard-only staging','inherited allocation or return transport'))
    return labels


def main():
    measured=defaultdict(set);evidence=[]
    for source in sys.argv[1:]:
        p=Path(source)
        if not p.exists():continue
        data=coverage.CoverageData(basename=str(p));data.read()
        for path in data.measured_files():measured[path].update(data.lines(path) or [])
        evidence.append(pin(p))
    rows=[];counts=Counter();files=[]
    for path in sorted((B/'code').rglob('*.py')):
        parser=PythonParser(filename=str(path));parser.parse_source();executable=set(parser.statements)
        missed=executable-measured[str(path)];groups=defaultdict(list);classification=labels(path)
        for n in sorted(missed):
            category,condition=classification.get(n,('UNEXPLAINED','No test or rehearsal executed this job-source line.'))
            groups[category,condition].append(n);counts[category]+=1
        for (category,condition),lines in groups.items():rows.append(dict(file=str(path.relative_to(B)),lines=lines,classification=category,condition=condition))
        files.append(dict(file=str(path.relative_to(B)),sha256=sha(path),statements=len(executable),executed=len(executable-missed),unexecuted=len(missed)))
    original=R/'from113/builds/02_c8r/out/coverage/review.py'
    value=dict(adapted_from=pin(original),evidence=evidence,counts=dict(counts),files=files,rows=rows,
               passed=counts['UNEXPLAINED']==0,scope='all packaged Python sources, including inherited dormant entry points and copied official scorers')
    dump(B/'out/UNEXECUTED.json',value)
    text=['Executable lines with no execution evidence. Sources and counts: `out/UNEXECUTED.json`.','',
          'This is a coverage census, not a claim that unexecuted GPU or remote branches passed. UNEXPLAINED remains a release blocker.','',
          '| File | Lines | Class | Condition |','|---|---|---|---|']
    for r in rows:text.append(f"| `{r['file']}` | {compact(r['lines'])} | {r['classification']} | {r['condition'].replace('|','/')} |")
    (B/'out/UNEXECUTED.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':main()
