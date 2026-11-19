from pathlib import Path
import sys,collections,json
L=Path(__file__).resolve().parents[2];D=L/"work/build24e";v=json.loads((D/"PATH_INVENTORY.json").read_text());rows=[r for r in v["records"] if r["resolution"]=="requires classification"]
for k,count in collections.Counter((r["kind"],"/".join(r["path"].split("/")[:4])) for r in rows).most_common(15):print(count,k)
for r in rows[:15]:print(r["where"],r["path"])
