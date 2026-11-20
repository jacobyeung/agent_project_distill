from common import *
p=L/'out/rcj/x.py';s=p.read_text().replace('    return subprocess.run(cmd, check=False).returncode','    return subprocess.run(cmd, check=False, env={**os.environ, "PATH":str(binary.parent)+os.pathsep+os.environ.get("PATH", "")}).returncode');replace(p,s)
