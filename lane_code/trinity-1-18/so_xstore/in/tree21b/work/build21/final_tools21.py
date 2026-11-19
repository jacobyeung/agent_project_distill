"""Prepare final upload names and refresh the source inventory without Git."""
from pathlib import Path
import json,sys,difflib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import digest,sha256
from student_pilot.source_seal import inventory
def refresh():
 files=inventory(T);seal=digest(files)
 (L/'out/TREE_FILES.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(files.items())))
 (L/'out/TREE_SEAL.json').write_text(json.dumps(dict(tree_sha256=seal,files=len(files)),indent=2)+'\n')
 print('source seal',seal)
if __name__=='__main__':refresh()
