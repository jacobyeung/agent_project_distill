from pathlib import Path
import sys,subprocess
L=Path(__file__).resolve().parents[2];D=L/"work/build24e"
s=(D/"sequence.py").read_text().replace("\x27sequence\x27","\x27sequence_final\x27").replace("/sequence/","/sequence_final/")
(D/"sequence_final.py").write_text(s)
raise SystemExit(subprocess.run([sys.executable,"-B",str(D/"sequence_final.py")]).returncode)
