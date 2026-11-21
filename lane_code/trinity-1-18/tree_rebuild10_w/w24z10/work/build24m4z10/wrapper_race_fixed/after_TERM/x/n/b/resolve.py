import sys
from pathlib import Path
Path(sys.argv[sys.argv.index("--output")+1]).write_text("{}")
