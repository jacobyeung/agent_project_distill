import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
LANE = Path('/scratch/jjyeung/orch_n30/b05_owngrd')
AUTH = LANE / 'work/auth'
TEACHER_K1 = LANE / 'work/manifests/TEACHER_K1.json'
FRAMES = LANE / 'work/frames'
