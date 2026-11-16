from pathlib import Path
import sys

lane = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(lane/'work/tree_r1'))
from student_pilot.r2_real_proof import main

try:
    main()
except (ValueError, FileNotFoundError) as error:
    print('REFUSED: '+str(error), file=sys.stderr)
    raise SystemExit(2)
