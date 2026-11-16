"""Write a passwd file whose jyeung entry is the authentic host NSS record (R229 host_identity_mounts logic)."""
import os
from pathlib import Path
import re
import subprocess
import sys

uid = os.getuid()
record = subprocess.check_output(['getent', 'passwd', str(uid)], text=True).strip()
match = re.fullmatch(r'([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*):([^:]*)', record)
if match is None or match.group(1) != 'jyeung' or int(match.group(3)) != uid:
    raise RuntimeError('The authentic host NSS identity does not match the assigned code-aws user')
rows = []
for row in re.findall(r'[^\n]+', Path('/etc/passwd').read_text()):
    head = re.match(r'([^:]*):[^:]*:([^:]*)', row)
    if head and (head.group(1) == match.group(1) or head.group(2) == str(uid)):
        continue
    rows.append(row)
rows.append(record)
path = Path(sys.argv[1]) / 'host_passwd'
path.write_text('\n'.join(rows) + '\n')
path.chmod(0o600)
print(str(path))
