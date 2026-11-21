"""Runs one kit script in a scratch walk. With A15_DIAG=1 the kit's own diagnose switch for the
census (cs.discovery) answers true in this process, and the script says so on its first line."""
import os, runpy, sys
from pathlib import Path

KIT = Path(os.environ['Q_KIT']).resolve()
sys.path.insert(0, str(KIT / 'b'))
import cs
if os.environ.get('A15_DIAG') == '1':
    cs.discovery = lambda kit: True
    print('A15 WARNING: census diagnose switch forced on for this scratch process', flush=True)
if os.environ.get('A15_DIAG') == '2':
    cs.discovery = lambda kit: True
    import sv
    native_classifier = sv.classifier

    def lenient(cfg):
        classify = native_classifier(cfg); seen = {'n': 0}

        def wrapped(row, stream):
            try:
                return classify(row, stream)
            except ValueError as error:
                if stream == 'pose' and str(error).startswith('R1_CENSUS_ROOM_UNRESOLVED'):
                    seen['n'] += 1
                    if seen['n'] in (1, 1000, 100000, 185667):
                        print('A15 WARNING: pose row with an unresolved room accepted with empty flags; count so far', seen['n'], flush=True)
                    return dict.fromkeys(sv.STATUSES, False)
                raise
        return wrapped
    sv.classifier = lenient
    print('A15 WARNING: census diagnose switch on, and unresolved pose rooms accepted with empty flags, for this scratch process', flush=True)
script = sys.argv[1]
sys.argv = [script, *sys.argv[2:]]
runpy.run_path(script, run_name='__main__')
