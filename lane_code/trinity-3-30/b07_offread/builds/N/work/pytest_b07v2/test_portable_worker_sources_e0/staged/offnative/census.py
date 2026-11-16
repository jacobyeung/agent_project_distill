"""Trace worker and native decoder lines without tracing unrelated dependencies."""
import ast
from pathlib import Path
import sys
from .io import dump,sha
from .paths import ROOT,C8,TREE,R
from .rehearse import run


def main():
    destination,kind,out=sys.argv[1:]
    files={str(p.resolve()):'offnative/'+p.name for p in (ROOT/'offnative').glob('*.py')}
    for base,prefix,names in (
        (C8,'c8r/',('perception.py','nomdg.py','reader_policy.py')),
        (TREE/'student_pilot','tree/student_pilot/',('carrier_c1_decode.py','carrier_c1_batch_decode.py',
              'live_trace313.py','live_instances314.py','routed_features.py','candidate_policy.py')),
        (R/'kit/revsi/launcher','reviewed_r/',('orchard_stage.py','s1.py','gate.py','export_stage.py'))):
        for name in names:files[str(base/name)]=prefix+name
    hits={}
    def trace(frame,event,arg):
        filename=frame.f_code.co_filename
        if filename not in files:return None
        if event=='line':hits.setdefault(filename,set()).add(frame.f_lineno)
        return trace
    sys.settrace(trace)
    try:run(destination,kind)
    finally:
        sys.settrace(None)
        records=[]
        for source,name in sorted(files.items(),key=lambda x:x[1]):
            p=Path(source);tree=ast.parse(p.read_text())
            statements={node.lineno for node in ast.walk(tree) if isinstance(node,ast.stmt)}
            executed=hits.get(source,set())
            records.append({'file':name,'sha256':sha(p),'executed_lines':sorted(executed),
                            'unexecuted_statement_lines':sorted(statements-executed)})
        dump(out,{'reader':kind,'scope':'Two-video synthetic whole-worker rehearsal; not a production-CONFIG rehearsal.',
                  'files':records,'production_config_transport_only':False})
if __name__=='__main__':main()
