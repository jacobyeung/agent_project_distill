from pathlib import Path
import shutil,hashlib,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24';T=L/'work/tree24';W=L.parent/'w23';inputs={}
p=T/'student_pilot/r1_population.py';s=p.read_text();s=s.replace("        if minimal and self.sources:\n            raise ValueError('R1_DEFERRED_MEMBERSHIP_NONEMPTY')", "        if minimal:\n            from .r1_coverage import deferred\n            deferred({'r1_training': {'routing_slices': 'deferred_first_boundary'}}, membership=value)");p.write_text(s)
p=T/'student_pilot/r1_rooms.py';s=p.read_text();s=s.replace('    from .r1_launch22 import validate_removals, bound\n    validate_removals(cfg)', '    from .r1_coverage import deferred\n    deferred(cfg, read_pins=True)\n    from .r1_launch22 import validate_removals, bound\n    validate_removals(cfg)');p.write_text(s)
script=(D/'merge23b.py').read_text();exec(compile(script[script.index("p=T/'student_pilot/r1_coverage.py'"):],str(D/'merge23b.py'),'exec'))
