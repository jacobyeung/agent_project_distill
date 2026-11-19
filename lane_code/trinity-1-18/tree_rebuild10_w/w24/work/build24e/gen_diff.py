from pathlib import Path
import difflib,sys
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";k=L/"work/build24/kits/q";g=D/"generated/q"
for p in g.rglob("*"):
 if p.is_file() and p.read_bytes()!=(k/p.relative_to(g)).read_bytes():
  print(p.relative_to(g))
  if p.suffix==".sh":print("".join(difflib.unified_diff((k/p.relative_to(g)).read_text().splitlines(True),p.read_text().splitlines(True))))
