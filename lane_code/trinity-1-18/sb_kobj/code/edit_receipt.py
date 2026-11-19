"""Record all inherited and local tree edits without Git."""
from common import *
import difflib

def main():
 pins();originals=js('/scratch/jjyeung/orch_n30/sb_ktow/inputs/CODE_SOURCES.json')['input_sha256'];changes=[];patch=[]
 for original,expected in originals.items():
  op=Path(original);candidate=None
  for marker in ('student_pilot/','e2e_reader/','trace_format/','heads/','rk/'):
   if marker in original:candidate=ROOT/'code/vendor'/(marker+original.split(marker,1)[1]);break
  if candidate is None or not candidate.exists():continue
  old=read(op).decode();assert PINS[str(op)]==expected
  new=candidate.read_text()
  if old==new:continue
  sm=difflib.SequenceMatcher(None,old.splitlines(),new.splitlines());hunks=[]
  for tag,i,j,a,b in sm.get_opcodes():
   if tag!='equal':hunks.append(dict(old_lines=[i+1,j],new_lines=[a+1,b],before=old.splitlines()[i:j],after=new.splitlines()[a:b]))
  changes.append(dict(source=str(op),copy=str(candidate.relative_to(ROOT)),source_sha256=expected,copy_sha256=sha(candidate),edits=hunks));patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(op),tofile=str(candidate.relative_to(ROOT))))
 write(ROOT/'out/EDITED_LINES.json',dict(changes=changes));(ROOT/'out/EDITED_LINES.patch').write_text(''.join(patch));print(len(changes),'changed copied files')
if __name__=='__main__':main()
