import sys; from pathlib import Path
root=Path(sys.argv[1]); sys.path.insert(0,str(root))
from student_pilot import source_seal, p3_provenance
inv=source_seal.inventory(root); print(sys.argv[1], len(inv), p3_provenance.digest(inv))
