"""Review bundle for the independent admission reviewer (trinity-3-3, Python 3.6). Written to OUT/review_bundle, then
copied to the lane directory with a paced tar | pv.

Contents: build report, frozen-input pins, uniformity proof, archive lists, both candidate indexes (gz), the
Trinity-only token map (gz), every export-P think text with its native qid, type and answer (gz), and 1,000 random full
rows from each export with the native qid attached.
usage: make_review_bundle.py SRC OUT
"""
import gzip
import json
import os
import random
import shutil
import sys
import tarfile


def main():
    src, out = sys.argv[1:3]
    bundle = os.path.join(out, "review_bundle")
    os.makedirs(bundle)
    for name in ("BUILD_REPORT.json", "FROZEN_INPUTS.json", "FRAMES_NEEDED.json"):
        shutil.copy(os.path.join(out, name), bundle)
    shutil.copy(os.path.join(src, "UNIFORMITY.json"), bundle)
    shutil.copy(os.path.join(src, "SUPPORT_ROW.json"), bundle)
    token_map = json.load(open(os.path.join(out, "MAP_TRINITY_ONLY.json")))
    with gzip.open(os.path.join(bundle, "MAP_TRINITY_ONLY.json.gz"), "wt") as stream:
        json.dump(token_map, stream, sort_keys=True)
    rng = random.Random(1027)
    for export in ("X", "P"):
        directory = os.path.join(out, "export_" + export)
        shutil.copy(os.path.join(directory, "ARCHIVES.json"), os.path.join(bundle, "ARCHIVES_%s.json" % export))
        shutil.copy(os.path.join(directory, "inherited_division.json"),
                    os.path.join(bundle, "inherited_division_%s.json" % export))
        with open(os.path.join(directory, "candidate_index.jsonl"), "rb") as source, \
                gzip.open(os.path.join(bundle, "candidate_index_%s.jsonl.gz" % export), "wb") as sink:
            shutil.copyfileobj(source, sink)
        archives = json.load(open(os.path.join(directory, "ARCHIVES.json")))
        total = sum(a["rows"] for a in archives)
        chosen = set(rng.sample(range(total), 1000))
        number = 0
        samples = open(os.path.join(bundle, "SAMPLE_ROWS_%s.jsonl" % export), "w")
        thinks = gzip.open(os.path.join(bundle, "THINK_P.jsonl.gz"), "wt") if export == "P" else None
        for archive in archives:
            with tarfile.open(os.path.join(directory, archive["file"])) as stream:
                for member in stream:
                    data = stream.extractfile(member).read()
                    row = json.loads(data.decode())
                    native = token_map["qids"].get(row["qid"])
                    if number in chosen:
                        samples.write(json.dumps({"member": member.name, "native_qid": native, "row": row}) + "\n")
                    if thinks is not None:
                        think = row["target"].split("</think>")[0][len("<think>\n"):].rstrip("\n")
                        thinks.write(json.dumps({"qid": row["qid"], "native_qid": native, "category": row["category"],
                                                 "answer": row["answer"], "think": think}) + "\n")
                    number += 1
        samples.close()
        if thinks is not None:
            thinks.close()
    with open(os.path.join(bundle, "README.txt"), "w") as stream:
        stream.write("Rung-1 review bundle. Exports X (A1/A2) and P (A3); full rows on trinity-3-3:%s/export_*.\n"
                     "SAMPLE_ROWS_<export>.jsonl: 1,000 random rows each, with native_qid from the Trinity-only map.\n"
                     "THINK_P.jsonl.gz: every export-P think text. candidate_index_<export>.jsonl.gz: full indexes.\n"
                     "MAP_TRINITY_ONLY.json.gz: opaque token -> native identifiers (never leaves Trinity).\n" % out)
    print("REVIEW_BUNDLE_DONE")


if __name__ == "__main__":
    main()
