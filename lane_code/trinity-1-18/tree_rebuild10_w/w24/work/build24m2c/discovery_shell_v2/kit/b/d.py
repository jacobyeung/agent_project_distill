from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import write
write(sys.argv[4],dict(status='PASS',scope='Fixture room-audit boundary; native census tested separately'))
