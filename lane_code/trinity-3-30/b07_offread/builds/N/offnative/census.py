"""Record executed source lines and distinguish fixtures from production evidence."""
import ast
from pathlib import Path
import sys
from .io import dump
from .paths import ROOT
from .rehearse import run

def main():
    destination,kind,out=sys.argv[1:]
    hits={}
    prefix=str(ROOT/'offnative')+'/'
    def trace(frame,event,arg):
        filename=frame.f_code.co_filename
        if not filename.startswith(prefix):
            return None
        if event=='line':
            hits.setdefault('offnative/'+filename[len(prefix):],set()).add(frame.f_lineno)
        return trace
    sys.settrace(trace)
    try:run(destination,kind)
    finally:
        sys.settrace(None)
        records=[]
        for p in sorted((ROOT/'offnative').glob('*.py')):
            tree=ast.parse(p.read_text())
            executable={node.lineno for node in ast.walk(tree) if isinstance(node,ast.stmt)}
            key=str(p.relative_to(ROOT));executed=hits.get(key,set())
            records.append(dict(file=key,executed_lines=sorted(executed),
                unexecuted_statement_lines=sorted(executable-executed)))
        dump(out,dict(reader=kind,scope='Two-video synthetic worker rehearsal; production transport-only rehearsal is NOT executed.',
                      files=records,orchard_only=['Production bootstrap and staging are unimplemented, so no executed-line claim is possible.',
                      'C8r HarnessReader.generate and replay require the real runtime context.',
                      'Build R governed_transfer requires the external IO governor and transport.']))
if __name__=='__main__':main()
