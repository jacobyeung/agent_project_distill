"""Spec for the visually blind prior (design record 4.1 'no-information baseline'; vl_eval.py --policy demo_replay):
for every task of a suite, the recorded LeRobot actions of the training subset's demos of that task. The evaluator
replays demo (trial mod n_demos) open loop from each evaluation init state: no images, no learning, only the task's
training data. usage: mk_blind_spec.py LEROBOT_DIR SUBSET_SPEC.json OUT.json"""
import collections, json, os, sys
import numpy as np, pyarrow.parquet as pq

d, spec_path, out = sys.argv[1:4]
spec = json.load(open(spec_path)); info = json.load(open(os.path.join(d, "meta/info.json")))
by_lang = collections.defaultdict(list)
for lang, eps in sorted(spec["per_task"].items()):
    for i in eps:
        f = os.path.join(d, info["data_path"].format(episode_chunk=i // info["chunks_size"], episode_index=i))
        a = np.stack(pq.read_table(f, columns=["action"]).column("action").to_numpy(zero_copy_only=False)).astype(np.float64)
        by_lang[lang].append({"episode_index": i, "actions": a.round(6).tolist()})
json.dump({"subset": os.path.basename(spec_path), "source": spec["source"], "by_lang": by_lang}, open(out, "w"))
print(out, {k[:40]: len(v) for k, v in by_lang.items()})
