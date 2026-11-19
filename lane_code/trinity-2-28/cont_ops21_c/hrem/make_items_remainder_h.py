"""Select the exact complement of an authenticated H partial."""
import argparse
import json
from pathlib import Path
from return_tools_h import segment, subset, require, TYPES
from fetch_validation import digest

def select(spec,work):
    rows,meta,info=segment(spec,work)
    full=info['manifest'];require('remainder' not in full,'Expected full H parent')
    require(not meta['publication']['complete'] and len(rows)<900,'Parent is complete')
    provenance=dict(parent_plan=info['plan'],parent_token=info['token'],parent_items_sha256=info['items_sha256'],
        partial_archive_sha256=digest(spec['archive']),partial_return_token=meta['publication']['token'],
        export_binding=info['export_binding'])
    done=[i['id'] for i in full['items'] if i['id'] in rows]
    return subset(full,done,provenance),rows,meta,info

def remaining_ids(m):
    return {k:[i["id"] for i in m["items"] if i["question_type"]==k] for k in TYPES}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('package','archive','exit','receipt','work','out'):p.add_argument('--'+n,required=True)
    a=p.parse_args();m,rows,meta,info=select(vars(a),a.work)
    with Path(a.out).open('x') as f:json.dump(m,f,indent=2,sort_keys=True);f.write('\n')
    id_path=Path(a.out).with_name(Path(a.out).stem+"_IDS.json")
    with id_path.open("x") as f:json.dump(remaining_ids(m),f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(dict(completed=len(rows),remaining=m['count'],per_type=m['per_type'],items_sha256=digest(a.out))))
if __name__=='__main__':main()
