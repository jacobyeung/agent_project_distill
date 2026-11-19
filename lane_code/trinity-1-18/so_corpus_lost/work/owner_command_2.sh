date -u
nice -n 10 env CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONDONTWRITEBYTECODE=1 python3 -I -s -B - /project/community/jjyeung/okh7/n2r/d627d31523064791d2ce3456/result.tar.gz <<'PY'
import base64, hashlib, json, re, sys, tarfile
total=0
with tarfile.open(sys.argv[1], "r|*") as archive:
    for m in archive:
        print(json.dumps({"member":m.name,"bytes":m.size,"regular":m.isfile()}), file=sys.stderr)
        name=m.name.lstrip("./")
        base=name.rsplit("/",1)[-1]
        selected=(base in {"SPEC.json","SUMMARY.json","COMPLETE.json","FAILED.json","IDENTITY.json","EXPORT_PIN.json","RETURN_ID.json","READ_IDENTITY.json","ORCHARD_NATIVE.json","ORCHARD_LAUNCHER.json","CARDS.json","READ_PLAN.json","environment.json","request.json","item_mapping.json","curve.json"} or re.search(r"(^|/)(items|items_sources|report)/[^/]+\.(json|jsonl)$", name) or base in {"TASKS.jsonl","CAMERA_TASKS.jsonl"})
        if not m.isfile() or not selected or m.size>8*1024*1024 or total+m.size>16*1024*1024:
            continue
        b=archive.extractfile(m).read(); total+=len(b)
        print(json.dumps({"archive":sys.argv[1],"member":m.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"base64":base64.b64encode(b).decode()}))
PY
