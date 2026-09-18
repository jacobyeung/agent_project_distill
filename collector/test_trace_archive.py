import base64
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from trace_archive import Archive, JournalList, install_archive, restore_snapshot  # noqa: E402


class Response:
    def __init__(self, text, *, thought=False, signature="sig"):
        self.text, self.thought, self.signature = text, thought, signature

    def model_dump(self, **_):
        return {"candidates": [{"content": {"parts": [{"text": self.text, "thought": self.thought,
                                                             "thought_signature": self.signature}]}}],
                "usage_metadata": {"prompt_token_count": 2, "candidates_token_count": 3,
                                   "total_token_count": 7, "thoughts_token_count": 1}, "model_version": "teacher-v1"}


class Models:
    def generate_content(self, **kwargs):
        if kwargs.get("fail"):
            raise RuntimeError("Bearer secret-token")
        return Response("visible", thought=True)

    def generate_content_stream(self, **kwargs):
        yield Response("first", thought=True)
        if kwargs.get("fail_after"):
            raise RuntimeError("after first")
        yield Response("second")


def _events(archive):
    return [json.loads(path.read_text()) for path in sorted(archive.events_dir.glob("*.json"))]


class TraceArchiveTest(unittest.TestCase):
    """Fixtures persist under /data2 so a failed run retains its evidence."""

    def setUp(self):
        self.fixture = Path("/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/trace_archive_fixtures") / str(time.time_ns())
        self.fixture.mkdir(parents=True)
        self.blobs = self.fixture / "archive_blobs"

    def archive(self, name, identity, *, trusted_roots=None):
        return Archive(self.fixture / name, identity, assets_root=self.blobs,
                       trusted_roots=trusted_roots or (self.fixture,))

    def test_records_native_thoughts_and_redacts_request(self):
        archive = self.archive("episode", {"qid": "q1"})
        with install_archive(archive, models_cls=Models):
            response = Models().generate_content(model="teacher", contents="ask", config={"api_key": "nope"})
        self.assertEqual(response.text, "visible")
        events = _events(archive)
        self.assertEqual([row["kind"] for row in events], ["provider_request", "provider_response", "provider_terminal"])
        self.assertEqual(events[0]["payload"]["kwargs"]["config"]["api_key"], "[REDACTED]")
        self.assertEqual({row["payload"]["call_id"] for row in events}, {events[0]["payload"]["call_id"]})
        self.assertEqual(events[-1]["payload"]["status"], "ok")
        part = events[1]["payload"]["response"]["candidates"][0]["content"]["parts"][0]
        self.assertEqual(part, {"text": "visible", "thought": True, "thought_signature": "sig"})
        self.assertEqual(events[1]["payload"]["response"]["usage_metadata"],
                         {"prompt_token_count": 2, "candidates_token_count": 3,
                          "total_token_count": 7, "thoughts_token_count": 1})

    def test_stream_keeps_chunk_before_error_and_interruption(self):
        failed = self.archive("failed", {"qid": "q2"})
        with install_archive(failed, models_cls=Models):
            with self.assertRaises(RuntimeError):
                list(Models().generate_content_stream(fail_after=True))
        self.assertEqual([row["kind"] for row in _events(failed)],
                         ["provider_request", "provider_chunk", "provider_error", "provider_terminal", "provider_interrupted"])
        failed_events = _events(failed)
        self.assertEqual(len({row["payload"]["call_id"] for row in failed_events}), 1)
        self.assertEqual(failed_events[-2]["payload"]["status"], "error")

        stopped = self.archive("stopped", {"qid": "q3"})
        with install_archive(stopped, models_cls=Models):
            stream = Models().generate_content_stream()
            next(stream)
            stream.close()
        self.assertEqual([row["kind"] for row in _events(stopped)],
                         ["provider_request", "provider_chunk", "provider_error", "provider_terminal", "provider_interrupted"])

    def test_assets_journal_lists_and_immutable_names(self):
        source = self.fixture / "frame.png"
        source.write_bytes(b"image bytes")
        mask = self.fixture / "mask.npy"
        mask.write_bytes(b"mask initial")
        archive = self.archive("assets", {"qid": "q4"})
        first = archive.asset(source, "image/png")
        second = archive.asset(b"image bytes", "image/png")
        self.assertEqual(first, second)
        other = self.archive("same-bytes", {"qid": "q5"})
        self.assertEqual(other.asset(b"image bytes", "image/png"), first)
        self.assertEqual(len([path for path in self.blobs.iterdir() if path.is_file()]), 1)
        rows = JournalList(archive, "assistant_message")
        message = {"role": "assistant", "tool_calls": [{"name": "measure", "args": {"id": 1}, "result": "3m"},
                                                         {"name": "crop", "args": {"frame": 4}, "result": "ok"}],
                   "visual": source, "mask_handle": f"mask stored at {source}",
                   "tool_content": json.dumps({"mask_handle": str(mask)}, separators=(",", ":")), "token": "discard"}
        rows.extend([message])
        message["tool_calls"][0]["result"] = "mutated"
        source.write_bytes(b"changed")
        mask.write_bytes(b"mask changed")
        event = _events(archive)[0]
        self.assertEqual(event["payload"]["token"], "[REDACTED]")
        self.assertEqual(event["payload"]["tool_calls"], [{"name": "measure", "args": {"id": 1}, "result": "3m"},
                                                             {"name": "crop", "args": {"frame": 4}, "result": "ok"}])
        self.assertEqual(event["payload"]["visual"]["sha256"], first["sha256"])
        self.assertEqual(event["payload"]["mask_handle"], f"mask stored at {source}")
        self.assertEqual(event["payload"]["tool_content"], json.dumps({"mask_handle": str(mask)}, separators=(",", ":")))
        self.assertEqual(Path(first["path"]).read_bytes(), b"image bytes")
        refs = [json.loads(line) for line in archive.artifact_refs_path.read_text().splitlines()]
        self.assertIn(str(source), [row["source_path"] for row in refs])
        mask_ref = next(row for row in refs if row["source_path"] == str(mask))
        self.assertEqual(Path(mask_ref["path"]).read_bytes(), b"mask initial")
        self.assertEqual(len(archive.journal_path.read_text().splitlines()), 1)

    def test_inline_image_roundtrips_through_shared_blob(self):
        archive = self.archive("inline", {"qid": "q6"})
        original = {"contents": {"inline_data": {"mime_type": "image/png",
                    "data": base64.b64encode(b"image bytes").decode("ascii")}, "raw_bytes": b"sidecar"}}
        archive.event("provider_request", original)
        saved = _events(archive)[0]["payload"]
        marker = saved["contents"]["inline_data"]["data"]
        self.assertEqual(marker["encoding"], "base64")
        self.assertEqual(restore_snapshot(saved), original)
        self.assertEqual(len([path for path in self.blobs.iterdir() if path.is_file()]), 2)

    def test_two_process_slow_publish_never_reads_a_partial_blob(self):
        module_dir = str(Path(__file__).parent)
        payload = b"same scene image bytes"
        workers = []
        for side in ("left", "right"):
            worker = f'''import json, os, sys, time
from pathlib import Path
sys.path.insert(0, {module_dir!r})
from trace_archive import Archive
fixture = Path({str(self.fixture)!r})
side = {side!r}
other = "right" if side == "left" else "left"
def slow(path, payload):
    midpoint = len(payload) // 2
    with path.open("xb") as handle:
        handle.write(payload[:midpoint]); handle.flush(); os.fsync(handle.fileno())
        ready = fixture / ("ready_" + side)
        with ready.open("xb") as flag:
            flag.write(b"ready"); flag.flush(); os.fsync(flag.fileno())
        deadline = time.monotonic() + 15
        while not (fixture / ("ready_" + other)).exists():
            if time.monotonic() > deadline: raise RuntimeError("process barrier timed out")
            time.sleep(0.01)
        handle.write(payload[midpoint:]); handle.flush(); os.fsync(handle.fileno())
Archive._stage_blob = staticmethod(slow)
archive = Archive(fixture / ("episode_" + side), {{"qid": side}},
                  assets_root=Path({str(self.blobs)!r}), trusted_roots=(fixture,))
print(json.dumps(archive.asset({payload!r}, "image/png"), sort_keys=True))'''
            workers.append(subprocess.Popen([sys.executable, "-B", "-c", worker], text=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1")))
        outputs = [worker.communicate(timeout=30) for worker in workers]
        self.assertEqual([(worker.returncode, stderr) for worker, (_, stderr) in zip(workers, outputs)], [(0, ""), (0, "")])
        refs = [json.loads(stdout) for stdout, _ in outputs]
        self.assertEqual(refs[0], refs[1])
        self.assertEqual(Path(refs[0]["path"]).read_bytes(), payload)

    def test_refuses_existing_episode_and_untrusted_asset(self):
        self.archive("one", {"qid": "q"})
        with self.assertRaises(FileExistsError):
            self.archive("one", {"qid": "q"})
        archive = self.archive("two", {"qid": "q"}, trusted_roots=(self.fixture / "safe",))
        with self.assertRaises(ValueError):
            archive.asset(self.fixture / "outside.txt")


if __name__ == "__main__":
    unittest.main()
