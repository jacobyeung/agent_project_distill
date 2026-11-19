from pathlib import Path
import datetime
import sys

root = Path(__file__).resolve().parent.parent
ready = (root / 'in/tree21b/READY').is_file()
stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
status = f'UTC {stamp}\nBuild 21b READY: {ready}\n\n' + '\n'.join(sys.argv[1:]) + '\n'
(root / 'work/STATUS.md').write_text(status)
print(status)
