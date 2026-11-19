from pathlib import Path
L=Path(__file__).resolve().parents[2];p=L/'work/tree_r1/student_pilot/r1_population.py';s=p.read_text()
a="""    from .r1_coverage import deferred, slice_bound
    minimal = deferred(cfg, read_pins=True)
    routing = load(pinned(cfg['streams']['routing']))
    if minimal and routing.get('source_membership'):
        slice_bound('streams.routing.source_membership', '<present>', 'R1_DEFERRED_MEMBERSHIP_NONEMPTY')
    receipt, _ = prepared(cfg)
"""
b="""    from .r1_coverage import deferred
    deferred(cfg, read_pins=True)
    receipt, _ = prepared(cfg)
"""
assert a in s;s=s.replace(a,b);p.write_text(s)
