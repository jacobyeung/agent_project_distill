"""Offline resumable protocol model. No sockets, credentials or actual GCS access.
Single-request PUT with Content-Length is legal without Content-Range.
REQUIRE_RANGE is a deliberately stronger fault-injection policy, not a GCS claim.
"""
import base64, fcntl, hashlib, json, os, re
from pathlib import Path


def crc32c(data):
    c = 0xffffffff
    for b in data:
        c ^= b
        for _ in range(8):
            c = (c >> 1) ^ (0x82f63b78 if c & 1 else 0)
    return base64.b64encode((c ^ 0xffffffff).to_bytes(4, "big")).decode()


class Reply:
    def __init__(self, status, data=b"", headers=None):
        self.status, self.data, self.headers = status, data, headers or {}
    def read(self, *a, **kw): return self.data
    def getheader(self, name, default=None): return self.headers.get(name, default)


class Connection:
    def __init__(self, host, timeout=600, **kw):
        self.headers, self.data, self.method = {}, bytearray(), None
        self.root = Path(os.environ["STRICT_SINK"])
        self.root.mkdir(exist_ok=True)
        self.host = host
    def putrequest(self, method, path):
        self.method = method
        self.name = path.split("?", 1)[0].lstrip("/")
    def putheader(self, name, value): self.headers[name.lower()] = str(value)
    def endheaders(self): pass
    def send(self, data): self.data.extend(data)
    def close(self): pass
    def getresponse(self):
        h = hashlib.sha256(self.name.encode()).hexdigest()
        with (self.root/(h+".lock")).open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state_path = self.root/(h+".json")
            state = json.loads(state_path.read_text()) if state_path.exists() else {"size": 0, "done": False}
            reply, reason = self.respond(state, self.root/(h+".bin"))
            state_path.write_text(json.dumps(state)+"\n")
            row = dict(name=self.name, method=self.method, length=len(self.data),
                       content_range=self.headers.get("content-range"), status=reply.status,
                       range=reply.getheader("Range"), reason=reason)
            with (self.root/"requests.jsonl").open("a") as f:
                fcntl.flock(f, fcntl.LOCK_EX); f.write(json.dumps(row)+"\n")
            return reply
    def respond(self, state, path):
        def error(code, reason): return Reply(code, json.dumps({"error":reason}).encode()), reason
        if self.method != "PUT": return error(405, "method")
        if self.host != "local.invalid": return error(404, "unknown_session")
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", self.name): return error(404, "name")
        try: length = int(self.headers["content-length"])
        except (KeyError, ValueError): return error(411, "length_required")
        if length != len(self.data): return error(400, "length_mismatch")
        cr = self.headers.get("content-range")
        query = bool(cr and re.fullmatch(r"bytes \*/(?:\d+|\*)", cr)) and length == 0
        if state["done"]:
            if query: return Reply(200, json.dumps(state["metadata"]).encode()), "completed_status"
            return error(410, "session_consumed")
        if query:
            hdr = {"Range": "bytes=0-%d" % (state["size"]-1)} if state["size"] else {}
            return Reply(308, headers=hdr), "incomplete_status"
        if self.headers.get("content-type") != "application/octet-stream": return error(400, "content_type")
        if not cr:
            if os.environ.get("REQUIRE_RANGE") == "1": return error(400, "explicit_range_policy")
            if state["size"]: return error(400, "range_required_after_partial")
            start, end, total = 0, length-1, length
        else:
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+|\*)", cr)
            if not match: return error(400, "range_syntax")
            start, end = map(int, match.group(1, 2))
            total = None if match[3] == "*" else int(match[3])
            if end < start or end-start+1 != length: return error(400, "range_length")
            if total is not None and end >= total: return error(400, "range_total")
        if start != state["size"]: return error(400, "range_offset")
        if state.get("total") is not None and total != state["total"]: return error(400, "total_changed")
        final = total is not None and end+1 == total
        if not final and length % (256*1024): return error(400, "chunk_alignment")
        with path.open("ab") as f: f.write(self.data)
        state["size"] += length
        if total is not None: state["total"] = total
        if not final:
            return Reply(308, headers={"Range": "bytes=0-%d" % (state["size"]-1)}), "incomplete"
        if os.environ.get("SINK_FAILURE") == "precondition": return error(412, "ifGenerationMatch")
        data = path.read_bytes()
        metadata = dict(size=str(len(data)), name=self.name, generation="1",
                        md5Hash=base64.b64encode(hashlib.md5(data).digest()).decode(), crc32c=crc32c(data))
        state.update(done=True, metadata=metadata)
        if os.environ.get("SINK_FAILURE") == "bad_md5": metadata["md5Hash"] = "invalid"
        if os.environ.get("SINK_FAILURE") == "bad_json": return Reply(200, b"invalid"), "bad_json"
        return Reply(200, json.dumps(metadata).encode()), "complete"
