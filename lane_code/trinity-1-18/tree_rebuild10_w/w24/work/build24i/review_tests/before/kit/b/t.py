from pathlib import Path
import sys
Path(sys.argv[2]).with_name("T_STARTED").write_text("t.py boundary; no training executed\n")
