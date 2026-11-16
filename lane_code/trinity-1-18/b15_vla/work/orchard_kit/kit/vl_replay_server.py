"""Stand-in policy server for the replay check: speaks StarVLA's websocket protocol (same handshake metadata keys as
server_policy.py) and answers each request with the next action chunk of the recorded demo named in the request
(example['replay_episode'], from step example['replay_t']). usage: vl_replay_server.py SPEC.json PORT [CHUNK]"""
import json, logging, sys
import numpy as np
from deployment.model_server.tools.websocket_policy_server import WebsocketPolicyServer

spec, port = json.load(open(sys.argv[1])), int(sys.argv[2])
chunk = int(sys.argv[3]) if len(sys.argv) > 3 else 8
acts = {e["episode_index"]: np.asarray(e["actions"], dtype=np.float32) for e in spec["episodes"]}

class ReplayPolicy:
    def predict_action(self, examples, **kw):
        ex = examples[0]; a = acts[int(ex["replay_episode"])]; t = int(ex["replay_t"])
        c = a[t : t + chunk]
        if len(c) < chunk:  # past the recorded end: hold still, gripper as last recorded
            pad = np.zeros((chunk - len(c), a.shape[1]), np.float32); pad[:, 6] = a[-1, 6]; c = np.concatenate([c, pad])
        return {"actions": c[None]}

logging.basicConfig(level=logging.INFO)
WebsocketPolicyServer(ReplayPolicy(), host="127.0.0.1", port=port, metadata={"action_chunk_size": chunk, "replay": True}).serve_forever()
