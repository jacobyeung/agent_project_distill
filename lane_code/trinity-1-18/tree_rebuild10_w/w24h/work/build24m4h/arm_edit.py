import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
p=L/'out/arm_routing.py';s=p.read_text()
s=s.replace('review_verdict,base_path=None):','review_verdict,base_path=None,regenerated_receipt_path=None):')
s=s.replace('''    if value.get("regenerated_sha256")!=reviewed_regenerated_sha256:
        raise ValueError("R1_REVIEWED_REGENERATED_DIFFERS")''','''    native = None
    if "regenerated_receipt" in value:
        if regenerated_receipt_path is None:raise ValueError("R1_REGENERATED_RECEIPT_REQUIRED")
        receipt_hash=pin(value["regenerated_receipt"],"R1_REGENERATED_RECEIPT_INVALID")
        receipt_path=Path(regenerated_receipt_path).resolve()
        receipt=J.load(J.checked(receipt_path,receipt_hash))
        receipt_digest=hashlib.sha256(json.dumps(receipt,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
        if receipt_digest!=value.get("regenerated_sha256"):raise ValueError("R1_REGENERATED_RECEIPT_DIGEST_DIFFERS")
        if receipt.get("schema")!="c1-routing-stream-v1" or receipt.get("stream")!="routing" or type(receipt.get("count")) is not int or receipt["count"]!=value.get("rows"):
            raise ValueError("R1_REGENERATED_RECEIPT_INVALID")
        output_hash=pin(receipt.get("database"),"R1_REGENERATED_RECEIPT_INVALID")
        if output_hash!=reviewed_regenerated_sha256:raise ValueError("R1_REVIEWED_REGENERATED_DIFFERS")
        native=dict(receipt=dict(path=str(receipt_path),sha256=receipt_hash),receipt_digest=receipt_digest,database_sha256=output_hash)
    elif value.get("regenerated_sha256")!=reviewed_regenerated_sha256:
        raise ValueError("R1_REVIEWED_REGENERATED_DIFFERS")''')
s=s.replace('''    if value["regenerated_sha256"]!=dh:raise ValueError("R1_ROUTING_REGENERATED_DATABASE_DIFFERS")''','''    if native is None:
        if value["regenerated_sha256"]!=dh:raise ValueError("R1_ROUTING_REGENERATED_DATABASE_DIFFERS")
    else:
        output_matches=[r for r in records if isinstance(r,dict) and r.get("sha256")==native["database_sha256"]]
        if not output_matches:raise ValueError("R1_DATABASE_METADATA_MISSING:"+native["database_sha256"])
        output_sizes={r.get("size") for r in output_matches}
        if len(output_sizes)!=1 or any(type(n) is not int or n<=0 for n in output_sizes):raise ValueError("R1_DATABASE_METADATA_SIZE_INVALID")
        native["database_bytes"]=next(iter(output_sizes))''')
s=s.replace('baseline="24m4e kits; apply UPLOADS_24M4E first"','baseline="24m4h kits; apply UPLOADS_24M4H and ORCHARD_COPIES_24M4H first"')
s=s.replace('        armed_n_go_config=config_hashes,','        armed_n_go_config=config_hashes,\n        native_regeneration=native,')
s=s.replace('    parser.add_argument("--review-verdict",required=True,type=Path)','    parser.add_argument("--review-verdict",required=True,type=Path)\n    parser.add_argument("--regenerated-receipt",type=Path,help="Published native receipt; required when the selection binds regenerated_receipt")')
s=s.replace('        review_verdict=args.review_verdict)','        review_verdict=args.review_verdict,regenerated_receipt_path=args.regenerated_receipt)')
replace(p,s)
print('Native receipt authentication added to arming helper')
