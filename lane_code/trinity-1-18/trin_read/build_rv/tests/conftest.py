import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Retained packet fixtures contain deliberate cyclic symlinks. Test modules live
# directly here; never collect generated evidence directories as test suites.
collect_ignore = [str(p) for p in Path(__file__).parent.iterdir() if p.is_dir()]
