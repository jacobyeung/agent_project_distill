from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build16'
s=(L/'work/build15/integrity15.py').read_text()
s=s.replace("B=L/'work/build15'","B=L/'work/build16'").replace('BUILD15_REPORT.md','BUILD16_REPORT.md').replace('work/build15/','work/build16/')
s=s[:s.index("(B/'STATUS.md').write_text")]
s += "\n(B/'STATUS.md').write_text((B/'STATUS.md').read_text()+'\\nPackage stream verification passed; see proofs/integrity/RESULT.json. GO=false remains.\\n')\n"
(B/'integrity16.py').write_text(s)
