"""Register one stopped transfer pipeline of this lane with the central IO governor, from the host it runs on
(Python 3.6, stdlib). Verifies the reader is stopped and owned by this user, that each member's stdin is the previous
process's stdout, and publishes streams/<lane>.json through a same-directory temporary file and rename. An existing
record for the same lane name is preserved by renaming it to <lane>.done.<unix time>.
usage: gov_register.py LANE TIER KIND NOMINAL_MBPS EXPECTED_BYTES PV_PID READER_PID [MEMBER_PID ...]
The pv process paces the pipeline; the governor sets its rate live with pv -R. Weights: a /data* read into
node-local scratch (io_weight 1, tunnel_weight 0). The governor, not this lane, resumes the stopped reader.
"""
import hashlib
import json
import os
import socket
import sys
import time

STREAMS = "/data3/jjyeung/orch_n13_20261026/io_governor/streams"


def identity(pid):
    base = "/proc/%d" % pid
    st = open(base + "/stat").read().rsplit(")", 1)[1].split()
    return {"pid": pid, "uid": os.stat(base).st_uid, "start_time": st[19], "state": st[0],
            "comm": open(base + "/comm").read().strip(), "cwd": os.readlink(base + "/cwd"),
            "cmd_sha256": hashlib.sha256(open(base + "/cmdline", "rb").read()).hexdigest(),
            "boot_id": open("/proc/sys/kernel/random/boot_id").read().strip()}


def main():
    lane, tier, kind, nominal = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4])
    expected_bytes, pv_pid = int(sys.argv[5]), int(sys.argv[6])
    pids = [int(p) for p in sys.argv[7:]]
    assert pv_pid in pids[1:], "pv must be a verified member of the pipeline"
    reader = identity(pids[0])
    assert reader["uid"] == os.getuid() and reader["state"] in ("T", "t"), "register only this lane's stopped reader"
    members = []
    for upstream, downstream in zip(pids, pids[1:]):
        out = os.readlink("/proc/%d/fd/1" % upstream)
        into = os.readlink("/proc/%d/fd/0" % downstream)
        assert out == into and out.startswith("pipe:"), (upstream, downstream, out, into)
        member = identity(downstream)
        assert member["uid"] == os.getuid()
        members.append(member)
    record = dict(reader, lane=lane, host=socket.gethostname().split(".")[0], tier=tier, kind=kind,
                  nominal_mbps=nominal, tunnel_mbps=0.0, resume_allowed=True, members=members, pv_pid=pv_pid,
                  expected_bytes=expected_bytes, io_weight=1.0, tunnel_weight=0.0, priority=10,  # rung-1 critical path (coordinator)
                  pipeline_verified="Each upstream fd1 matches downstream fd0; same UID; reader is the lane's gated "
                                    "tar_reader.py or tar, pacer is pv, sink is tar xf into node-local /scratch.")
    path = os.path.join(STREAMS, lane + ".json")
    if os.path.exists(path):
        os.rename(path, path[:-len(".json")] + ".done.%d" % int(time.time()))
    with open(path + ".next", "w") as stream:
        stream.write(json.dumps(record, indent=2) + "\n")
    os.replace(path + ".next", path)
    print(path)


if __name__ == "__main__":
    main()
